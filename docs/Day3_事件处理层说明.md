# Day 3：事件处理层实现说明

> 对应 MVP 一周计划 Day 3「事件处理层」。
>
> 技术栈：**FastAPI + LangChain 结构化输出 + SQLAlchemy**
>
> 日期：2026-06-24

---

## 1. 完成内容

Day 3 实现了事件处理层的完整链路：**读未处理 raw_news → LLM 结构化抽取 → 标题相似度去重合并 → 写 events / event_sources → HTTP 接口触发与查询**。

### 1.1 新建文件清单

| 文件 | 作用 |
|------|------|
| `backend/config/prompts/event_extraction.txt` | 事件抽取 Prompt 模板（与代码分离，可配置） |
| `backend/app/processors/__init__.py` | 事件处理层包初始化 |
| `backend/app/processors/event_extractor.py` | 单条新闻 → LLM 结构化抽取 → `ExtractedEvent` |
| `backend/app/processors/event_dedup.py` | 字符 bigram 覆盖度相似度 + 合并判定 |
| `backend/app/processors/event_processor.py` | 编排：读未处理 → 抽取 → 合并 → 写库 |
| `backend/app/schemas/event.py` | `ExtractedEvent` / `EventOut` / 抽取统计 Pydantic 模型 |
| `backend/app/api/v1/events.py` | `GET /api/events` + `POST /api/jobs/extract` |
| `backend/tests/unit/test_event_dedup.py` | 去重合并判定单测（8 例） |
| `docs/Day3_事件处理层说明.md` | 本文档 |

### 1.2 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/main.py` | 挂载 `events_router`（`/api` 前缀，`events` tag） |
| `backend/pyproject.toml` | 新增 `[tool.pytest.ini_options]`（pythonpath、testpaths） |

### 1.3 无新增依赖

复用 Day 1/2 已有依赖：`langchain`（结构化输出）、`sqlalchemy`、`fastapi`、`pydantic`。去重用纯 Python 字符 bigram，不引分词库。

---

## 2. 架构说明

### 2.1 数据流

```
未处理 raw_news（id ∉ event_sources.raw_news_id）
    ↓ 逐条
LLM 结构化抽取（create_structured_model(ExtractedEvent)）
    → ExtractedEvent(title, type, subject, time, summary)
    ↓ event_type == "other" ? → 跳过噪声（不建事件、不写关联）
合并判定：候选池(本批次已生成 + DB 近7天 events)
         中找同 event_type 且标题覆盖度 ≥ 0.6 者
    ├─ 命中 → INSERT event_sources，source_count += 1（合并）
    └─ 未命中 → 新建 Event(EVT_YYYYMMDD_NNN) + event_sources
    ↓
db.commit()（失败 rollback，整批统计归零但已处理条数仍记录）
```

### 2.2 LLM 结构化抽取

复用 Day 1 的 LLM 工厂 `app.services.llm.create_structured_model`：

- 传入 `ExtractedEvent`（pydantic schema），底层调用 `chat_model.with_structured_output(schema)`。
- `invoke([HumanMessage(prompt)])` 直接返回 `ExtractedEvent` 实例，**无需自解析 JSON**，schema 校验由 LangChain 保证。
- 结构化模型在模块级惰性构造一次复用，避免每条新闻重建。
- Prompt 模板外置 `config/prompts/event_extraction.txt`，启动时 `lru_cache` 读取一次。
- `event_time` 为空时回退 `raw_news.published_at`。
- 单条抽取异常时记日志返回 `None`，**不中断整批**（异常隔离，与 Day 2 采集层同思路）。

### 2.3 去重合并：字符 bigram 覆盖度

合并键 = `event_type` 相同 + 标题字符 bigram **覆盖度** ≥ 0.6。

**为什么用覆盖度而非 Jaccard：** 真实新闻标题常一长一短（同一事件不同详略），Jaccard 分母被长串的额外 bigram 拉大，对长度差敏感。覆盖度 `max(|A∩B|/|A|, |A∩B|/|B|)` 衡量"短串的核心 bigram 是否都在长串里"，对详略不同更鲁棒。

实测区分度（见单测）：

| 标题对 | 覆盖度 | 判定 |
|--------|--------|------|
| "美国宣布对华加征关税" vs "美国对华加征关税政策正式宣布" | 0.78 | 合并 ✓ |
| "美国发布新能源补贴政策细则" vs "美国新能源补贴政策正式发布" | 0.67 | 合并 ✓ |
| "美联储宣布加息25个基点" vs "美联储主席发表讲话" | 0.25 | 不合并 ✓ |
| "美联储宣布加息25个基点" vs "某公司发布新款手机产品" | 0.00 | 不合并 ✓ |

**设计取舍：**
- 偏激进合并（宁可并多一点），避免重复生成大量相似事件卡片（呼应计划 4.2 节）。
- `event_subject` 抽取并存，但**不作合并键**：LLM 对主体命名不稳定（"中国" vs "中国政府"会漏合并）。
- 字符级 bigram 不引分词依赖，对中英文都鲁棒。

### 2.4 已处理判定（零迁移）

**不加 `raw_news` 状态字段、不加迁移**：用「`raw_news.id` 是否已存在于 `event_sources.raw_news_id`」反查已处理。

- 未处理 = `NOT EXISTS (SELECT 1 FROM event_sources WHERE raw_news_id = raw_news.id)`
- 抽取失败 / 判为噪声（`other`）的新闻不写关联 → 下次仍会被取出重试。
- 优点：零 schema 变更；失败自动重试，符合 Day 6 演示复现要求。

### 2.5 event_id 展示码

`EVT_YYYYMMDD_NNN`：按当天日期 + 当日序号（查当日同前缀最大序号 +1，定宽 3 位）。展示码业务唯一，外键仍指向整型 `id`（与现有模型约定一致）。

### 2.6 合并候选池

取 DB **近 7 天**既有事件 + 本批次已生成事件作为候选池。本批次内加入候选，使同一批里的重复新闻互相合并；限定近 7 天避免与太久远事件误并。

---

## 3. 接口说明

### 3.1 `POST /api/jobs/extract`

手动触发一次事件抽取处理。无请求体。

**响应示例：**

```json
{
  "processed": 8,
  "new_events": 5,
  "merged": 3,
  "skipped_noise": 1,
  "failed": 0
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `processed` | int | 本轮实际处理（抽取成功且非噪声）的新闻数 |
| `new_events` | int | 本轮新建事件数 |
| `merged` | int | 本轮合并到既有事件的次数 |
| `skipped_noise` | int | 被 LLM 判定为非事件（`other`）而跳过的条数 |
| `failed` | int | 抽取/入库失败被隔离的条数 |

### 3.2 `GET /api/events`

事件列表，按 `created_at` 倒序。

**查询参数：**

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `event_type` | str | 无 | 按事件类型过滤（policy/trade/...） |
| `limit` | int | 50 | 返回条数上限（1-200） |

**响应示例：**

```json
[
  {
    "id": 1,
    "event_id": "EVT_20260624_001",
    "event_title": "美国宣布对华加征关税",
    "event_type": "trade",
    "event_subject": "美国",
    "event_time": "2026-06-24T08:30:00",
    "summary": "事件摘要……",
    "source_count": 3,
    "status": "new",
    "created_at": "2026-06-24T10:00:00"
  }
]
```

---

## 4. 验证结果

### 4.1 单元测试

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/unit/test_event_dedup.py -v
```

8 例全部通过，覆盖：相同标题、高重叠合并、不相关、空串、同类型合并、不同类型不合并、低相似不合并、多候选取最高分。

### 4.2 端到端验证

从 `backend/` 目录：

```bash
# 1) 先采集新闻（Day 2）
curl -X POST http://localhost:8000/api/jobs/collect

# 2) 触发事件抽取
curl -X POST http://localhost:8000/api/jobs/extract

# 3) 查看事件列表
curl http://localhost:8000/api/events

# 4) 重复抽取：已处理新闻不再抽取，无重复事件
curl -X POST http://localhost:8000/api/jobs/extract
```

### 4.3 数据库抽查

```sql
SELECT count(*) FROM events;
SELECT count(*) FROM event_sources;
SELECT event_id, event_title, event_type, source_count FROM events ORDER BY created_at DESC LIMIT 5;
```

每个事件的 `source_count` 应等于其在 `event_sources` 中的关联行数。

### 4.4 实测结果

以真实 RSS 数据 + DeepSeek 抽取跑通全链路：

- `raw_news=52`，`events=41`，`event_sources=42`（42-41=1 次合并命中）
- 四个路由 `/health`、`GET /api/events`、`POST /api/jobs/collect`、`POST /api/jobs/extract` 全部 200
- 事件标题为客观概括而非照抄原标题，例如：
  - `EVT_20260624_039 | company` → "中芯国际向国家集成电路基金等5名股东发行5.47亿股收购中芯北方49%股权…"
  - `EVT_20260624_041 | company` → "思源电气董事兼副总经理杨帜华计划减持不超过13万股"

---

## 5. 如何运行

```bash
cd backend

# 安装依赖（含 dev：pytest 等）
uv pip install -e ".[dev]" --python .venv/Scripts/python.exe

# 首次：配置 .env（至少 DEEPSEEK_API_KEY，或切换 llm.yaml 的 provider）
cp .env_example .env

# 启动服务
.venv/Scripts/python.exe -m uvicorn app.main:app --reload

# 触发抽取
curl -X POST http://localhost:8000/api/jobs/extract
```

---

## 6. 已知问题与后续

1. **LLM 依赖外部 API** — 抽取需 `DEEPSEEK_API_KEY`（或其他 provider）就绪；密钥缺失或限流时该条计 `failed`，不中断批次。
2. ~~**LLM 返回 None 时崩溃**~~ — ✅ Day 4 测试发现 `model.invoke()` 在 API Key 未配置时返回 `None` 而非抛异常，导致 `result.event_time` 报 `AttributeError`。已修复：在 `event_extractor.py` 中 `invoke()` 后增加 `if result is None` 提前返回。
2. **合并阈值固定 0.6** — `event_dedup.py` 的 `MERGE_THRESHOLD` 常量，后续可按语料调优或外置到配置。
3. **候选池窗口 7 天** — `_MERGE_LOOKBACK_DAYS`，超过 7 天的相似事件不会合并，后续可配置化。
4. **同步处理** — 逐条 LLM 调用，大批量时较慢；MVP 可接受，必要时引入队列（计划第 8 节）。
5. ~~**无事件详情/卡片接口~~ — ✅ Day 5 已实现 `GET /api/events/{id}`、`GET /api/events/{id}/card`。

---

## 7. 与 Day 4 的衔接

Day 4 推理分析层从 `events` 表读取结构化事件，调用 LLM 生成重要性评分、影响行业/资产、因果链、风险提示，写入 `event_analysis`（与 `events` 一对一）。Day 3 产出的 `event_title` / `event_type` / `summary` / `event_subject` 直接作为 Day 4 分析的输入。Day 6 一键演示链路为：`collect → extract → analyze → 展示`，本层的 `POST /api/jobs/extract` 是其中间环节。
