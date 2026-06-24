# EventAlpha 数据库设计与用法

> 对应 MVP 一周计划 Day 1「项目骨架与数据模型」。
>
> 技术栈：**SQLAlchemy 2.0（同步引擎）+ Alembic + SQLite**（起步，可迁移 PostgreSQL）。
>
> 当前范围：仅数据层（模型 + 迁移 + SQLite 文件），不含 FastAPI / 采集 / 分析等业务逻辑。

---

## 1. 概述

EventAlpha MVP 的核心链路是「采集原始新闻 → 抽取结构化事件 → 生成投资影响分析 → 展示事件卡片」。数据库承载这条链路的四个实体：

| 数据表 | 所属层 | 职责 | 与其他表关系 |
|--------|--------|------|--------------|
| `raw_news` | 数据采集层 | 原始新闻入库（来源、标题、摘要、链接、时间、内容哈希） | 被 `event_sources` 引用 |
| `events` | 事件处理层 | 结构化事件（标题、类型、主体、时间、摘要、来源数、状态） | 1—N `event_sources`，1—1 `event_analysis` |
| `event_sources` | 事件处理层 | 事件与原始新闻的多源关联 | N—1 `events`，N—1 `raw_news` |
| `event_analysis` | 推理分析层 | 事件投资影响分析（重要性、影响行业/资产、因果链、风险提示） | 1—1 `events` |

另外有 Alembic 自动管理的 `alembic_version` 表，记录当前迁移版本，不属于业务表。

实体关系：

```text
┌──────────┐ 1     N ┌──────────────┐ N     1 ┌──────────┐
│  events  │─────────│ event_sources │─────────│ raw_news │
└──────────┘         └──────────────┘         └──────────┘
     │ 1
     │
     │ 1
┌────────────────┐
│ event_analysis │
└────────────────┘
```

---

## 2. 设计决策

### 2.1 同步引擎（非 async）

MVP 是「采集→处理→分析」的批处理流水线，没有高并发 HTTP 需求；Alembic autogenerate 在同步引擎下最简单。未来上 PostgreSQL 时可保持同步，或切异步，schema 无需改动。

### 2.2 主键策略：整型 id + 业务唯一键

每张表用整型自增 `id` 作真正主键；`events` 额外有展示码 `event_id`（如 `EVT_20260624_001`，`VARCHAR(32)` + UNIQUE + INDEX）。

- 外键（`event_sources`、`event_analysis`）指向整型 `events.id`，而非展示码 `event_id`——连接更便宜、展示码可重新格式化、对 PostgreSQL 友好（`SERIAL`/`IDENTITY`）。
- `event_id` 作为人类可读的业务唯一键保留。

### 2.3 SQLite 外键强制

SQLite **默认不强制外键约束**，会导致 `ON DELETE CASCADE` 静默失效。在 [app/core/database.py](../backend/app/core/database.py) 注册了 `connect` 事件监听器，每条连接建立时执行 `PRAGMA foreign_keys=ON`。验证：`PRAGMA foreign_keys` 返回 `(1,)`。

### 2.4 批量模式迁移（render_as_batch）

SQLite 的 `ALTER TABLE` 几乎不支持（不能加 NOT NULL 无默认列、删列、改类型、加外键）。Alembic env.py 设置 `render_as_batch=True`，变更以「重建表」方式实现；对 PostgreSQL 无害。

### 2.5 JSON 列可移植性

`event_analysis` 的数组字段（影响行业、影响资产、因果链、正负因素）用 SQLAlchemy 便携 `JSON` 类型：SQLite 存为 TEXT，PostgreSQL 存为 `json`。**未使用** PG 专属 `JSONB`，保证可迁移。将来若要换 JSONB，属于类型变更，需在 SQLite 走批模式。

### 2.6 时区：UTC naive

采用 **UTC naive datetime** 约定（`DateTime` 不带 `timezone=True`）：

- SQLite 无原生 datetime 类型，`DateTime(timezone=True)` 在 SQLite 上被忽略（存为文本）。
- SQLite 的 `func.now()` `server_default` 写入的是**连接本地时间**而非 UTC。
- 因此 `created_at` / `collected_at` 用 Python `default=utcnow`（`datetime.now(timezone.utc).replace(tzinfo=None)`）。
- `published_at` 来自 RSS 解析，在 Day 2 入库时归一为 UTC naive。

### 2.7 去重键

- `raw_news.content_hash`（SHA-256 hex，64 字符）设 **UNIQUE**，是主去重键。
- `raw_news.url` 设**普通索引**（非 unique）：同一文章可能经多个 URL 联合分发，unique 会误拒合法重复。

### 2.8 一对一与一对一约束

- `event_analysis.event_id` 上的 FK 同时加 UNIQUE INDEX，在 DB 层强制「一事件一分析」。
- `event_sources` 上 `UNIQUE(event_id, raw_news_id)` 防止同一新闻重复归属同一事件。
- `event_analysis.importance_score` 上 `CHECK (BETWEEN 1 AND 5)`，可移植，随 CREATE TABLE 生成、批模式重建表时保留。

### 2.9 配置外置

数据库 URL 由 `.env` 的 `DATABASE_URL` 提供，是单一真相源。`alembic.ini` 的 `sqlalchemy.url` 留空，由 [alembic/env.py](../backend/alembic/env.py) 从 `Settings` 注入。应用代码与迁移脚本共用同一配置。

---

## 3. 表结构详解

### 3.1 `raw_news`（原始新闻）

| 列 | 类型 | 约束 / 默认 | 说明 |
|----|------|-------------|------|
| `id` | INTEGER | PK, autoincrement | 主键 |
| `source` | VARCHAR(128) | NOT NULL | 新闻来源名称 |
| `title` | VARCHAR(512) | NOT NULL | 标题 |
| `summary` | TEXT | nullable | 摘要 |
| `url` | VARCHAR(1024) | NOT NULL, INDEX | 链接（非唯一） |
| `content_hash` | VARCHAR(64) | NOT NULL, UNIQUE INDEX | 内容哈希，主去重键 |
| `published_at` | DATETIME | nullable, INDEX | 发布时间（UTC naive） |
| `collected_at` | DATETIME | NOT NULL, default=utcnow | 采集时间（UTC naive） |

模型：[app/models/raw_news.py](../backend/app/models/raw_news.py)

### 3.2 `events`（结构化事件）

| 列 | 类型 | 约束 / 默认 | 说明 |
|----|------|-------------|------|
| `id` | INTEGER | PK, autoincrement | 主键 |
| `event_id` | VARCHAR(32) | NOT NULL, UNIQUE INDEX | 展示码 `EVT_20260624_001` |
| `event_title` | VARCHAR(512) | NOT NULL | 事件标题 |
| `event_type` | VARCHAR(64) | NOT NULL, INDEX | 事件类型（policy/war/trade/rate/tech/company_announcement/disaster） |
| `event_subject` | VARCHAR(256) | nullable | 主体（国家/公司/机构/行业） |
| `event_time` | DATETIME | nullable, INDEX | 事件发生时间（UTC naive） |
| `summary` | TEXT | nullable | 事件摘要 |
| `source_count` | INTEGER | NOT NULL, default 1 | 来源数（冗余计数） |
| `status` | VARCHAR(32) | NOT NULL, default 'new', INDEX | 事件状态 |
| `created_at` | DATETIME | NOT NULL, default=utcnow | 创建时间（UTC naive） |

`event_type` 用字符串而非 Enum，便于扩展且便于迁移。

模型：[app/models/event.py](../backend/app/models/event.py)

### 3.3 `event_sources`（事件—新闻关联）

| 列 | 类型 | 约束 / 默认 | 说明 |
|----|------|-------------|------|
| `id` | INTEGER | PK, autoincrement | 主键 |
| `event_id` | INTEGER | NOT NULL, FK→events.id ON DELETE CASCADE, INDEX | 事件（整型 id） |
| `raw_news_id` | INTEGER | NOT NULL, FK→raw_news.id ON DELETE CASCADE, INDEX | 原始新闻（整型 id） |
| `source_name` | VARCHAR(128) | nullable | 来源名 |
| `created_at` | DATETIME | NOT NULL, default=utcnow | 关联时间 |

表级约束：`UNIQUE(event_id, raw_news_id)` 名为 `uq_event_source_pair`。

带元数据（`source_name`、`created_at`），故用完整模型而非裸关联表。

模型：[app/models/event_source.py](../backend/app/models/event_source.py)

### 3.4 `event_analysis`（事件分析）

| 列 | 类型 | 约束 / 默认 | 说明 |
|----|------|-------------|------|
| `id` | INTEGER | PK, autoincrement | 主键 |
| `event_id` | INTEGER | NOT NULL, FK→events.id ON DELETE CASCADE, UNIQUE INDEX | 事件（强制一对一） |
| `importance_score` | INTEGER | NOT NULL, CHECK 1—5 | 重要性评分 1-5 |
| `importance_level` | VARCHAR(2) | NOT NULL, INDEX | 重要性等级 S/A/B/C |
| `affected_industries` | JSON | NOT NULL, default '[]' | 受影响行业 |
| `affected_assets` | JSON | NOT NULL, default '[]' | 受影响资产 |
| `causal_chain` | JSON | NOT NULL, default '[]' | 因果链（数组） |
| `positive_factors` | JSON | NOT NULL, default '[]' | 正面因素 |
| `negative_factors` | JSON | NOT NULL, default '[]' | 负面因素 |
| `risk_warning` | TEXT | nullable | 风险提示 |
| `model_version` | VARCHAR(64) | nullable | 生成分析的模型版本 |
| `created_at` | DATETIME | NOT NULL, default=utcnow | 创建时间（UTC naive） |

表级约束：`CHECK (importance_score BETWEEN 1 AND 5)` 名为 `ck_importance_score_1_5`。

模型：[app/models/event_analysis.py](../backend/app/models/event_analysis.py)

### 3.5 `alembic_version`（迁移版本，Alembic 管理）

| 列 | 类型 | 约束 |
|----|------|------|
| `version_num` | VARCHAR(32) | NOT NULL, PK |

非业务表，由 Alembic 维护，勿手动改。

---

## 4. 事件卡片字段映射

MVP 计划中的事件卡片 JSON 对应到如下表的字段：

```json
{
  "event_id": "EVT_20260624_001",       // events.event_id
  "title": "某国宣布新的关税政策",       // events.event_title
  "event_type": "trade_tariff",         // events.event_type
  "summary": "事件摘要",                // events.summary
  "source_count": 3,                    // events.source_count
  "importance_level": "A",              // event_analysis.importance_level
  "importance_score": 4,                // event_analysis.importance_score
  "affected_industries": ["..."],       // event_analysis.affected_industries (JSON)
  "affected_assets": ["..."],           // event_analysis.affected_assets (JSON)
  "causal_chain": ["..."],              // event_analysis.causal_chain (JSON)
  "positive_factors": ["..."],          // event_analysis.positive_factors (JSON)
  "negative_factors": ["..."],          // event_analysis.negative_factors (JSON)
  "risk_warning": "..."                 // event_analysis.risk_warning
}
```

卡片由 `events` 与其唯一的 `event_analysis` 拼装而成。

---

## 5. 快速开始

> **所有命令一律从 `backend/` 目录运行**，否则 `.env` 找不到、SQLite 文件位置会偏移。

### 5.1 环境要求

- Python ≥ 3.12
- [uv](https://github.com/astral-sh/uv)（推荐，已用于本项目）或 pip

### 5.2 安装依赖

```bash
cd backend
uv sync            # 创建 .venv 并安装依赖，生成 uv.lock
```

依赖（仅数据层）：`sqlalchemy`、`alembic`、`pydantic`、`pydantic-settings`、`greenlet`。

### 5.3 配置

`.env`（已 gitignore，不入库）由 `.env_example` 复制而来：

```bash
# backend/.env
DATABASE_URL=sqlite:///./eventalpha.db
```

- `sqlite:///./eventalpha.db`（三斜杠 + 相对路径）解析为 `<运行目录>/eventalpha.db`，即 `backend/eventalpha.db`。
- 迁移到 PostgreSQL 时改为：`postgresql+psycopg://user:password@host:5432/eventalpha`。

### 5.4 建库（应用迁移）

```bash
cd backend
uv run alembic upgrade head
```

执行后在 `backend/` 下生成 `eventalpha.db`，包含全部 4 张业务表 + `alembic_version`。

---

## 6. 常用命令（均在 `backend/` 下）

| 命令 | 作用 |
|------|------|
| `uv run alembic upgrade head` | 应用到最新迁移（建库） |
| `uv run alembic upgrade <revision>` | 应用到指定版本 |
| `uv run alembic downgrade -1` | 回退一个版本 |
| `uv run alembic downgrade base` | 回退到初始（删全部表） |
| `uv run alembic revision --autogenerate -m "说明"` | 对比模型与 DB 自动生成迁移 |
| `uv run alembic current` | 查看当前已应用版本 |
| `uv run alembic history` | 查看迁移历史 |

**修改模型后的流程**：改 `app/models/` → `uv run alembic revision --autogenerate -m "..."` → **人工检查生成的迁移文件** → `uv run alembic upgrade head`。

> autogenerate 不是万能的：CHECK 约束、某些类型变更、数据迁移需要手动补。生成后务必打开 `alembic/versions/*.py` 核对 upgrade/downgrade 是否完整。

---

## 7. 在代码中使用

### 7.1 会话与依赖

[app/core/database.py](../backend/app/core/database.py) 提供：

- `engine`、`SessionLocal`（`expire_on_commit=False`，便于任务代码提交后读属性）
- `Base`（`DeclarativeBase`）
- `get_db()`（FastAPI 依赖生成器，Day 2 产品服务层可直接复用）
- `utcnow()`（UTC naive 时间助手）

```python
from app.core.database import SessionLocal, get_db, utcnow
```

### 7.2 写入示例

```python
from app.core.database import SessionLocal
from app.models import RawNews, Event, EventSource, EventAnalysis

with SessionLocal() as db:
    news = RawNews(
        source="reuters",
        title="Fed holds rates steady",
        url="https://example.com/fed",
        content_hash="a" * 64,          # SHA-256 hex
        summary="The Fed kept rates unchanged.",
    )
    event = Event(
        event_id="EVT_20260624_001",
        event_title="Fed holds rates",
        event_type="rate",
        event_subject="Fed",
        summary="Rates unchanged",
    )
    db.add_all([news, event])
    db.flush()                          # 拿到自增 id

    db.add(EventSource(event_id=event.id, raw_news_id=news.id, source_name="reuters"))
    db.add(EventAnalysis(
        event_id=event.id,
        importance_score=4,
        importance_level="A",
        affected_industries=["banks"],
        affected_assets=["XLF"],
        causal_chain=["rates flat", "yield curve stable"],
        positive_factors=["financials"],
        negative_factors=[],
        risk_warning="该分析仅用于事件研究，不构成投资建议。",
        model_version="demo-1",
    ))
    db.commit()
```

JSON 数组字段直接传 Python `list`，SQLAlchemy 自动序列化；读取时自动还原为 `list`。

### 7.3 关系遍历

```python
with SessionLocal() as db:
    event = db.get(Event, 1)
    print(event.analysis.affected_industries)   # 一对一
    print([s.raw_news.title for s in event.sources])  # 一对多关联
```

### 7.4 级联删除

删除 `events` 行时，`event_sources` 与 `event_analysis` 中对应行会被 `ON DELETE CASCADE` 自动清除（依赖 §2.3 的 PRAGMA 监听器）。

---

## 8. 验证（已通过）

| 检查项 | 命令 | 预期 |
|--------|------|------|
| 表清单 | `sqlite3 eventalpha.db ".tables"` | `alembic_version event_analysis event_sources events raw_news` |
| 完整结构 | `sqlite3 eventalpha.db ".schema"` | 4 张表 CREATE + 索引 + FK + CHECK |
| 外键 | `sqlite3 eventalpha.db "PRAGMA foreign_key_list(event_sources);"` | 两条 FK，均 `CASCADE` |
| 索引 | `sqlite3 eventalpha.db "PRAGMA index_list(raw_news);"` | `content_hash` unique=1，`url` unique=0 |
| 外键开关 | `uv run python -c "from app.core.database import engine; from sqlalchemy import text; print(engine.connect().execute(text('PRAGMA foreign_keys')).fetchone())"` | `(1,)` |
| 迁移状态 | `uv run alembic current` | `<hash> (head)` |
| ORM 端到端 | 插入 → 重复对被拒 / score=6 被拒 / 第二份分析被拒 / 删事件后关联与分析归零 | 全部如预期 |

---

## 9. 文件清单

| 文件 | 作用 |
|------|------|
| [backend/pyproject.toml](../backend/pyproject.toml) | 依赖与项目元数据 |
| [backend/.env](../backend/.env) / [.env_example](../backend/.env_example) | 数据库 URL 配置 |
| [backend/app/core/config.py](../backend/app/core/config.py) | `Settings`，从 `.env` 读 `DATABASE_URL` |
| [backend/app/core/database.py](../backend/app/core/database.py) | 引擎、会话、`Base`、外键 PRAGMA、`get_db`、`utcnow` |
| [backend/app/models/](../backend/app/models/) | 4 张表的 ORM 模型 + `__init__.py`（注册到 `Base.metadata`） |
| [backend/alembic.ini](../backend/alembic.ini) | Alembic 配置（URL 留空，由 env.py 注入） |
| [backend/alembic/env.py](../backend/alembic/env.py) | 迁移环境：注入 URL、导入模型、`render_as_batch`、`compare_type` |
| [backend/alembic/script.py.mako](../backend/alembic/script.py.mako) | 迁移脚本模板 |
| [backend/alembic/versions/](../backend/alembic/versions/) | 迁移脚本目录（含初始建表迁移） |

---

## 10. 迁移到 PostgreSQL

数据层已为迁移预留：

1. 安装驱动：`uv add psycopg`（或 `psycopg2-binary` / `asyncpg`）。
2. 改 `backend/.env`：`DATABASE_URL=postgresql+psycopg://user:password@host:5432/eventalpha`。
3. `uv run alembic upgrade head` 在空库上重建全部表。
4. 如需迁移存量数据，用 `pgloader` 或导出 SQL 脚本导入。

注意点：

- JSON 列：当前用便携 `JSON`（PG 上为 `json`）。若要 `jsonb`（支持索引、更快），改模型类型后生成迁移，SQLite 端会走批模式重建表。
- 外键：PG 默认强制外键，§2.3 的 PRAGMA 监听器在 PG 上是空操作，无需移除。
- 时区：若 PG 端要用 `timestamptz`，把 `DateTime` 改为 `DateTime(timezone=True)` 并统一写入带时区的 UTC datetime——这是一次类型变更，需迁移。
- `check_same_thread=False` 是 SQLite 专属参数，PG 引擎会忽略，无需改代码。

---

## 11. 注意事项与陷阱

- **SQLite 外键默认关闭** → 靠 `database.py` 的 connect 监听器开启，否则 CASCADE 失效。
- **SQLite ALTER 受限** → `render_as_batch=True` 让后续迁移以「重建表」实现。
- **DB 文件位置随 CWD** → 一律从 `backend/` 运行；`eventalpha.db` 落在 `backend/`，已被 `.gitignore` 的 `*.db` 忽略，不入库。
- **时区** → UTC naive + Python `default=utcnow`，避免 SQLite `func.now()` 的本地时间问题。
- **autogenerate 需人工复核** → 重点看 CHECK 约束、类型变更、数据迁移是否完整，downgrade 是否对称。
- **新增模型** → 在 `app/models/` 建文件，并在 [app/models/__init__.py](../backend/app/models/__init__.py) 追加 import 与 `__all__`，否则 autogenerate 发现不到。
- **`event_sources.source_count` 冗余** → `events.source_count` 是冗余计数，由事件处理层在合并来源时维护，不靠 COUNT 实时算（MVP 简化）。
