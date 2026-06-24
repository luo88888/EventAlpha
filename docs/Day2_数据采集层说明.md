# Day 2：数据采集层实现说明

> 对应 MVP 一周计划 Day 2「数据采集层」。
>
> 技术栈：**FastAPI + feedparser + httpx + SQLAlchemy**
>
> 日期：2026-06-24

---

## 1. 完成内容

Day 2 实现了数据采集层的完整链路：**RSS 拉取 → 内容去重 → 原始新闻入库 → HTTP 接口触发**。

### 1.1 新增依赖

在 `backend/pyproject.toml` 中新增：

| 依赖 | 版本 | 用途 |
|------|------|------|
| `fastapi` | >=0.115 | Web 框架 |
| `uvicorn[standard]` | >=0.34 | ASGI 服务器 |
| `feedparser` | >=6.0 | RSS/Atom 解析 |
| `httpx` | >=0.28 | HTTP 客户端（拉取 RSS） |

开发依赖新增 `pytest`、`pytest-asyncio`。

### 1.2 新建文件清单

| 文件 | 作用 |
|------|------|
| `backend/app/main.py` | FastAPI 入口：挂载路由、启动时建表、健康检查 `/health` |
| `backend/app/collectors/__init__.py` | 包初始化 |
| `backend/app/collectors/rss_collector.py` | RSS 采集器核心逻辑 |
| `backend/app/api/__init__.py` | 包初始化 |
| `backend/app/api/v1/__init__.py` | 包初始化 |
| `backend/app/api/v1/collect.py` | `POST /api/jobs/collect` 采集接口 |
| `backend/app/schemas/__init__.py` | 包初始化 |
| `backend/app/schemas/raw_news.py` | Pydantic 响应模型 |

---

## 2. 架构说明

### 2.1 数据流

```
RSS Feed (httpx 拉取)
    ↓
feedparser 解析条目
    ↓
SHA-256(title + url) → content_hash
    ↓
内存去重：seen_hashes / seen_urls 是否已见？
    ├─ 已见 → skip（同一批次内的重复条目）
    └─ 未见 → 查 raw_news 表：content_hash 是否存在？
                  ├─ 存在 → skip
                  └─ 不存在 → 再查 url 是否存在？
                                ├─ 存在 → skip
                                └─ 不存在 → INSERT raw_news
    ↓
db.commit()（失败则 rollback，不影响其他源）
```

### 2.2 去重策略

采用三级去重：

1. **内存去重：seen_hashes / seen_urls**
   - 同一批 feed 内可能包含重复条目（如 BBC RSS 返回两条 title+url 完全相同的新闻）
   - 在进入 DB 查询前用 set 拦截，避免 SQLAlchemy session 内出现两条相同 content_hash 导致 commit 时 UNIQUE 约束冲突
2. **主去重：content_hash**（SHA-256 of `title|url`）
   - `raw_news.content_hash` 字段有 UNIQUE 约束
   - 即使同一新闻标题略有不同，只要 title+url 组合一致就不会重复入库
3. **备用去重：url 索引查询**
   - content_hash 未命中时，按 url 再查一次
   - 防止同一文章通过不同 RSS 源以不同标题分发

### 2.3 错误隔离

每个 RSS 源的采集（`collect_source`）是独立的：

- **网络错误**：`_fetch_feed()` 失败时记录日志并跳过该源，不影响其他源
- **入库错误**：`db.commit()` 失败时执行 `db.rollback()` 回滚该源的数据，记录日志，后续源正常采集
- 这保证了单个源的问题不会导致整个采集请求 500，也不会污染数据库会话

### 2.4 RSS 源配置

在 `rss_collector.py` 的 `RSS_SOURCES` 列表中配置，每个源包含 `name`（写入 source 字段）和 `url`（RSS 地址）：

| 源 | URL | 状态 |
|----|-----|------|
| reuters | `https://feeds.reuters.com/reuters/topNews` | ⚠️ SSL 错误，跳过 |
| bbc | `https://feeds.bbci.co.uk/news/rss.xml` | ⚠️ 网络不可达，返回 0 条 |
| cnbc | `https://search.cnbc.com/rs/search/combinedcms/view.xml?...` | ✅ 正常 |
| aljazeera | `https://www.aljazeera.com/xml/rss/all.xml` | ⚠️ 网络不可达，返回 0 条 |

> reuters/bbc/aljazeera 在当前网络环境下不可达，但不会导致采集崩溃。后续可替换为其他可用源或使用代理。

---

## 3. 接口说明

### 3.1 `POST /api/jobs/collect`

手动触发一次 RSS 采集。

**请求：** 无请求体。

**响应示例：**

```json
{
  "results": [
    {"source": "reuters", "fetched": 0, "new": 0, "skipped": 0},
    {"source": "bbc", "fetched": 0, "new": 0, "skipped": 0},
    {"source": "cnbc", "fetched": 30, "new": 4, "skipped": 26},
    {"source": "aljazeera", "fetched": 0, "new": 0, "skipped": 0}
  ],
  "total_fetched": 30,
  "total_new": 4,
  "total_skipped": 26
}
```

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `results` | list | 每个源的采集统计 |
| `results[].source` | str | 源名称 |
| `results[].fetched` | int | RSS 返回的条目数 |
| `results[].new` | int | 新写入 raw_news 的条数 |
| `results[].skipped` | int | 因去重跳过的条数 |
| `total_*` | int | 各字段的汇总 |

### 3.2 `GET /health`

健康检查。

**响应：** `{"status": "ok"}`

---

## 4. 验证结果

### 4.1 首次采集

```bash
curl -X POST http://localhost:8000/api/jobs/collect
```

- CNBC 返回 30 条，4 条新入库，26 条去重跳过
- 其他 3 个源返回 0 条（网络不可达，但不崩溃）

### 4.2 去重验证

再次调用采集接口：

- CNBC 再次拉到 30 条，但全部因 content_hash 重复被跳过（`new=0, skipped=30`）
- 数据库总数保持不变

### 4.3 数据库验证

```sql
SELECT count(*) FROM raw_news;
SELECT source, title, content_hash FROM raw_news LIMIT 3;
```

每条记录包含完整的 source、title、summary、url、content_hash、published_at、collected_at 字段。

### 4.4 Bug 修复验证

**修复前的问题：**
1. BBC RSS 返回重复条目 → `db.commit()` 时 UNIQUE 约束冲突 → 整个请求 500
2. `db.commit()` 在 try/except 外面 → 单个源失败导致所有源数据丢失

**修复后的单元测试：**

| 测试场景 | 结果 |
|----------|------|
| Feed 内 3 条相同条目 | ✅ 只插入 1 条，跳过 2 条（内存去重） |
| 源 2 commit 失败，源 3 正常 | ✅ 源 2 被隔离（rollback），源 3 正常采集 |

---

## 5. 如何运行

```bash
cd backend

# 安装依赖（conda agent 环境）
/home/liuke/miniconda3/envs/agent/bin/pip install -e ".[dev]"

# 首次：创建 .env
cp .env_example .env

# 运行迁移（如果 Day 1 已执行则跳过）
/home/liuke/miniconda3/envs/agent/bin/python -m alembic upgrade head

# 启动服务
/home/liuke/miniconda3/envs/agent/bin/uvicorn app.main:app --reload

# 测试采集
curl -X POST http://localhost:8000/api/jobs/collect
```

---

## 6. 已知问题与后续

1. **3 个 RSS 源不可达** — reuters（SSL 错误）、bbc、aljazeera 在当前网络环境下无法访问，但不会导致采集崩溃。后续可替换为其他可用源或使用代理。
2. **无错误重试** — 单个源拉取失败会记录日志但不重试，MVP 阶段可接受。
3. **采集限流** — 未做请求间隔控制，如果源很多需要注意频率。
4. **摘要 HTML 清理** — feedparser 的 summary 字段可能含 HTML 标签，当前用正则简单去除，复杂场景可能需要更完善的清理。
5. ~~**Feed 内重复条目导致 UNIQUE 冲突**~~ — ✅ 已修复（内存去重 set）
6. ~~**db.commit() 未捕获异常导致整个请求 500**~~ — ✅ 已修复（try/except + rollback）

---

## 7. 与 Day 3 的衔接

Day 3 事件处理层需要从 `raw_news` 表读取原始新闻，调用 LLM 抽取结构化事件写入 `events` 和 `event_sources` 表。Day 2 采集入库的数据直接可供 Day 3 使用。
