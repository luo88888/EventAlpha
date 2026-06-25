# Day 3：事件处理层 — 工作拆解

## 🎯 目标

将 `raw_news` 表中的 127 条原始新闻转成结构化事件，写入 `events` + `event_sources`，并实现去重合并。

## 📦 需要新建的文件

```
backend/
├── config/prompts/
│   └── event_extraction.txt        # 事件抽取 Prompt 模板
├── app/processors/
│   ├── __init__.py
│   └── event_extractor.py          # 核心：raw_news → events 处理逻辑
└── app/api/v1/
    └── events.py                   # 事件列表/详情 API（交付物之一）
```

---

## 任务清单

### 1. 设计事件抽取 Prompt

**文件**：`config/prompts/event_extraction.txt`

**内容**：给 LLM 一条新闻（标题 + 摘要），要求输出：

| 字段 | 说明 | 示例 |
|------|------|------|
| `event_title` | 事件标题，简洁概括 | "泰国央行维持利率1.00%不变" |
| `event_type` | 事件类型（枚举） | `monetary_policy` |
| `event_subject` | 事件主体 | "泰国央行" |
| `event_time` | 事件发生时间（ISO 格式，可空） | `2026-06-24` |
| `summary` | 一句话摘要 | "泰国央行决定维持政策利率于1.00%，符合市场预期" |

**事件类型枚举**（MVP 阶段覆盖主要类型）：

```
monetary_policy    # 货币政策（利率、QE）
fiscal_policy      # 财政政策（税收、补贴）
trade_tariff       # 贸易/关税
geopolitics        # 地缘政治（冲突、制裁）
corporate_action   # 公司行为（财报、并购、IPO）
industry_news      # 行业动态（技术突破、产能变化）
macro_data         # 宏观数据（GDP、CPI、就业）
natural_disaster   # 自然灾害
regulation         # 监管政策
other              # 其他
```

**要点**：
- Prompt 需要求 LLM 以 JSON 格式输出，方便解析
- 考虑批量处理：一次喂 3-5 条新闻，减少 LLM 调用次数
- 处理 LLM 返回异常（JSON 解析失败、字段缺失）的兜底逻辑

---

### 2. 实现事件抽取器 `event_extractor.py`

**职责**：读 raw_news → 调 LLM → 写 events + event_sources

**核心流程**：

```
1. 查询 status='pending' 的 raw_news（未处理过的）
2. 分批（每批 3-5 条）构造 Prompt，调 LLM
3. 解析 LLM 返回的 JSON，构建 Event 对象
4. 去重判断：是否已有相似事件？
   - 简单策略：同 event_type + 同 event_subject + 时间接近 → 合并
   - 合并：source_count++，新增 event_sources 关联
   - 不合并：新建 Event，source_count=1
5. 写入 events + event_sources
6. 标记已处理的 raw_news（避免重复处理）
```

**需要解决的问题**：

| 问题 | 方案 |
|------|------|
| raw_news 没有 `status` 字段 | 方案 A：新增 `processed` 布尔字段（需改模型+迁移）<br>方案 B：用 event_sources 反查已处理的 news_id（无需改表） |
| LLM 调用失败 | 单条失败不阻塞整批，记录日志跳过，下次重试 |
| LLM 返回格式异常 | JSON 解析失败 → 跳过该条，记录 warning |
| 事件去重粒度 | MVP 用简单规则：(event_type, event_subject) 相近 + 时间差 < 24h |

**关键函数**：

```python
def process_pending_news(db: Session, batch_size: int = 5) -> dict:
    """处理未抽取的 raw_news，返回统计 {processed, merged, created, errors}"""

def extract_events_from_batch(news_batch: list[RawNews]) -> list[dict]:
    """对一批新闻调 LLM，返回抽取结果列表"""

def find_or_create_event(db: Session, extracted: dict, raw_news: RawNews) -> Event:
    """去重：找到已有事件则合并，否则新建"""

def build_extraction_prompt(news_batch: list[RawNews]) -> str:
    """构造抽取 Prompt（加载模板 + 填充新闻内容）"""
```

---

### 3. 去重合并逻辑

**策略**（MVP 简化版）：

```
对每条抽取结果：
  1. 查 events 表：event_type 相同 AND event_subject 相同 AND event_time 差 < 24h
  2. 找到 → 合并：
     - event.source_count += 1
     - 新增 event_sources 记录
  3. 没找到 → 新建 Event：
     - event_id = f"EVT_{日期}_{序号}"
     - source_count = 1
     - status = "new"
     - 新增 event_sources 记录
```

**注意**：
- `event_id` 是展示码（如 `EVT_20260624_001`），需要序号自增逻辑
- `event_sources` 有 `(event_id, raw_news_id)` 唯一约束，重复插入会报错

---

### 4. 手动触发接口

**文件**：`app/api/v1/events.py`

**新增端点**：

| 端点 | 用途 |
|------|------|
| `POST /api/jobs/process` | 手动触发事件抽取（调用 `process_pending_news`） |
| `GET /api/events` | 事件列表（按类型、时间、重要性筛选，分页） |
| `GET /api/events/{event_id}` | 事件详情（含 sources 列表） |

`POST /api/jobs/process` 响应：

```json
{
  "status": "ok",
  "processed": 127,
  "created": 42,
  "merged": 15,
  "errors": 0
}
```

---

### 5. 模型调整（如需要）

**如果选择给 raw_news 加 `processed` 字段**：

- 修改 `app/models/raw_news.py`：新增 `processed: Mapped[bool]`，默认 False
- 生成迁移：`alembic revision --autogenerate -m "add processed to raw_news"`
- 检查迁移文件 → 执行迁移

**如果用 event_sources 反查方案**：无需改表，但查询略复杂。

**建议**：加 `processed` 字段，简单直观，且后续重试场景更方便。

---

## 依赖关系

```
任务 1（Prompt）  ──┐
                     ├──→ 任务 2（抽取器）──→ 任务 4（API）
任务 3（去重逻辑）──┘
任务 5（模型调整）──→ 任务 2（抽取器）
```

- 任务 1 和 3 可并行
- 任务 5 影响任务 2，需先决定方案
- 任务 4 依赖任务 2 完成

## 技术要点

- **LLM 调用**：用已有的 `app/services/llm/factory.py` 的 `create_structured_model()`，直接输出 Pydantic 对象
- **Prompt 模板加载**：参考 `utils/config_handler.py` 的模式，或直接 `Path("config/prompts/xxx.txt").read_text()`
- **批量处理**：减少 LLM 调用次数，每批 3-5 条新闻合并到一个 Prompt
- **日志**：用 `logging.getLogger(__name__)` 记录处理进度和异常

## 验收标准

- [ ] 127 条 raw_news 全部处理完成（可通过 `POST /api/jobs/process` 触发）
- [ ] 生成的 events 表有合理数量的事件（去重后预计 40-60 条）
- [ ] 重复新闻被合并到同一事件（source_count > 1）
- [ ] `GET /api/events` 可返回事件列表
- [ ] `GET /api/events/{id}` 可返回事件详情含来源
- [ ] LLM 调用失败不影响其他新闻的处理
