# Day 4：推理分析层实现说明

> 对应 MVP 一周计划 Day 4「推理分析层」。
>
> 技术栈：**FastAPI + LangChain 结构化输出 + SQLAlchemy**
>
> 日期：2026-06-25

---

## 1. 完成内容

Day 4 实现了推理分析层的完整链路：**读未分析事件 → LLM 投资影响分析 → 写 event_analysis → HTTP 接口触发**。

### 1.1 新建文件清单

| 文件 | 作用 |
|------|------|
| `backend/config/prompts/event_analysis.txt` | 事件分析 Prompt 模板（与代码分离，可配置） |
| `backend/app/analysis/__init__.py` | 推理分析层包初始化 |
| `backend/app/analysis/event_analyzer.py` | 单事件 → LLM 分析 → `AnalyzedEvent` |
| `backend/app/analysis/analysis_processor.py` | 编排：读未分析 → 逐条分析 → 写库 |
| `backend/tests/unit/test_analyze_prompt.py` | Schema 约束、Prompt 加载、异常隔离单测（6 例） |
| `backend/tests/integration/test_analyze_api.py` | API 集成测试（7 例） |
| `docs/Day4_推理分析层说明.md` | 本文档 |

### 1.2 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/schemas/event.py` | 追加 `AnalyzedEvent`（LLM 输出 schema）、`AnalyzeResult`、`AnalyzeResponse` |
| `backend/app/api/v1/events.py` | 追加 `POST /api/jobs/analyze` 端点 |

### 1.3 无新增依赖

复用 Day 1/2/3 已有依赖：`langchain`（结构化输出）、`sqlalchemy`、`fastapi`、`pydantic`。

---

## 2. 架构说明

### 2.1 数据流

```
未分析事件（events.id ∉ event_analysis.event_id）
    ↓ 逐条
LLM 结构化分析（create_structured_model(AnalyzedEvent)）
    → AnalyzedEvent(importance_score, importance_level, affected_industries,
                     affected_assets, causal_chain, positive/negative_factors, risk_warning)
    ↓
构建 EventAnalysis（补充 model_version、created_at）
    ↓
db.commit()（失败 rollback，整批统计归零）
```

### 2.2 LLM 结构化分析

复用 Day 1 的 LLM 工厂 `app.services.llm.create_structured_model`：

- 传入 `AnalyzedEvent`（pydantic schema），底层调用 `chat_model.with_structured_output(schema)`。
- `invoke([HumanMessage(prompt)])` 直接返回 `AnalyzedEvent` 实例，**无需自解析 JSON**，schema 校验由 LangChain 保证。
- 结构化模型在模块级惰性构造一次复用，避免每次重建。
- Prompt 模板外置 `config/prompts/event_analysis.txt`，启动时 `lru_cache` 读取一次。
- 单条分析异常时记日志返回 `None`，**不中断整批**（异常隔离，与 Day 3 抽取器同思路）。

### 2.3 已分析判定（零迁移）

**不加 `events` 状态字段、不加迁移**：用「`events.id` 是否已存在于 `event_analysis.event_id`」反查已分析。

- 未分析 = `NOT EXISTS (SELECT 1 FROM event_analysis WHERE event_id = events.id)`
- 分析失败的事件不写入关联 → 下次仍会被取出重试。
- 优点：零 schema 变更；失败自动重试。

### 2.4 model_version 记录

每次分析时从 `load_llm_config()` 读取当前 provider/model，拼接为 `"{provider}/{model}"` 写入 `event_analysis.model_version`。便于后续对比不同模型的分析质量。

### 2.5 AnalyzedEvent schema 约束

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `importance_score` | int | 1-5（Pydantic `ge=1, le=5`） | 与 DB 的 CHECK 约束一致 |
| `importance_level` | str | S/A/B/C（Prompt 约束） | 与 score 对应：5→S，4→A，3→B，2/1→C |
| `affected_industries` | list[str] | 可空列表 | 中文行业名称 |
| `affected_assets` | list[str] | 可空列表 | 中文资产/公司名称 |
| `causal_chain` | list[str] | 至少 1 步 | 有序传导链 |
| `positive_factors` | list[str] | 可空列表 | 正面因素 |
| `negative_factors` | list[str] | 可空列表 | 负面因素 |
| `risk_warning` | str | 非空 | 必须以"不构成投资建议"结尾 |

---

## 3. 接口说明

### 3.1 `POST /api/jobs/analyze`

手动触发一次事件分析处理。无请求体。

**响应示例：**

```json
{
  "analyzed": 41,
  "skipped_existing": 0,
  "failed": 0
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `analyzed` | int | 本轮分析成功的事件数 |
| `skipped_existing` | int | 已有分析而跳过的事件数（当前实现：已分析事件不进入处理列表，此字段恒为 0） |
| `failed` | int | 分析失败的事件数 |

---

## 4. 验证结果

### 4.1 单元测试

```bash
cd backend
/home/liuke/miniconda3/envs/agent/bin/python -m pytest tests/unit/test_analyze_prompt.py -v
```

6 例全部通过，覆盖：schema 合法构造、score 越界（0 和 6）、空列表合法、Prompt 模板可加载且含占位符、LLM 异常返回 None。

### 4.2 集成测试

```bash
cd backend
/home/liuke/miniconda3/envs/agent/bin/python -m pytest tests/integration/test_analyze_api.py -v
```

7 例全部通过，覆盖：首次分析、分析后详情/卡片有值、跳过已有分析、无事件可分析、LLM 失败隔离、幂等性。

### 4.3 全量测试

```bash
cd backend
/home/liuke/miniconda3/envs/agent/bin/python -m pytest tests/ -v
```

35 例全部通过（Day 2 去重 8 + Day 3 API 14 + Day 4 单测 6 + Day 4 集成 7）。

### 4.4 端到端验证（真实 LLM）

使用 DeepSeek API，在真实数据上跑通全链路。

**单条抽取测试（随机 5 条）：**

| # | 来源 | 标题 | 抽取结果 |
|---|------|------|----------|
| 1 | cnbc | FedEx posts strong earnings... | ✅ 联邦快递发布财报，type=company |
| 2 | aljazeera | Cristiano Ronaldo becomes first... | ✅ C罗世界杯进球，type=other（噪声跳过） |
| 3 | bbc | Clean sweep for Mamdani-backed... | ✅ 纽约民主党初选，type=other |
| 4 | aljazeera | NBA Draft 2026... | ✅ NBA选秀，type=other |
| 5 | cnbc | Ukraine is raising the cost... | ✅ 乌克兰对俄战争，type=geopolitical |

5/5 成功，LLM 正确区分事件与噪声。

**单条分析测试（构造事件）：**

```
输入：美联储宣布加息25个基点（type=rate）

输出：
  重要性：A 级（4分）
  影响行业：银行、房地产、债券、外汇、大宗商品、股票市场
  影响资产：美元指数、美国国债收益率、黄金、沪深300、标普500、纳斯达克指数、新兴市场货币、人民币汇率
  因果链：美联储加息 → 短期利率走高 → 企业融资成本上升 → 美元资产吸引力增强 → 新兴市场承压 → 全球股票估值面临压力
  正面因素：加息符合预期消除不确定性、银行净息差扩大
  负面因素：融资成本上升、房地产承压、新兴市场资本外流、成长股估值承压
  风险提示：需关注后续美联储政策路径...该分析仅用于事件研究，不构成投资建议。
```

**Bug 修复：** 测试中发现 Day 3 的 `event_extractor.py` 在 LLM 返回 `None` 时（如 API Key 未配置）会崩溃（`AttributeError: 'NoneType' object has no attribute 'event_time'`），已修复为提前检查 `result is None`。

**全量抽取 + 分析：**

```bash
# 1) 触发事件抽取（127 条 raw_news → 结构化事件）
curl -X POST http://localhost:8000/api/jobs/extract

# 2) 触发事件分析
curl -X POST http://localhost:8000/api/jobs/analyze

# 3) 查看事件详情（应含 analysis）
curl http://localhost:8000/api/events/1

# 4) 查看事件卡片（应含 importance_level 等）
curl http://localhost:8000/api/events/1/card
```

### 4.5 前端验证

```bash
cd frontend
npm run dev
```

访问 `http://localhost:3000/events/1`，确认分析卡片正常展示（不再降级为 EmptyAnalysis），包含重要性徽章、影响行业/资产标签、因果链步骤、正负因素列表、风险提示。

---

## 5. 与 Day 5 的对齐

Day 5 前端已实现的组件与 Day 4 输出完全对齐，**前端零改动**：

| 前端组件 | 读取字段 | Day 4 写入来源 |
|----------|----------|----------------|
| `ImportanceBadge` | `importance_level`, `importance_score` | `AnalyzedEvent` → `EventAnalysis` |
| `AnalysisCard` → `TagList` | `affected_industries`, `affected_assets` | `AnalyzedEvent` → `EventAnalysis` (JSON) |
| `CausalChain` | `causal_chain` | `AnalyzedEvent` → `EventAnalysis` (JSON) |
| `FactorList` | `positive_factors`, `negative_factors` | `AnalyzedEvent` → `EventAnalysis` (JSON) |
| `AnalysisCard` | `risk_warning`, `model_version` | `AnalyzedEvent` + `analysis_processor` → `EventAnalysis` |
| `EmptyAnalysis` | `analysis === null` | 未分析事件仍走降级，已分析事件自动切换 |

---

## 6. 如何运行

```bash
cd backend

# 安装依赖（含 dev：pytest 等）
/home/liuke/miniconda3/envs/agent/bin/pip install -e ".[dev]"

# 首次：配置 .env（至少 DEEPSEEK_API_KEY，或切换 llm.yaml 的 provider）
cp .env_example .env

# 启动服务
/home/liuke/miniconda3/envs/agent/bin/uvicorn app.main:app --reload

# 触发分析
curl -X POST http://localhost:8000/api/jobs/analyze
```

---

## 7. 已知问题与后续

1. **LLM 依赖外部 API** — 分析需 `DEEPSEEK_API_KEY`（或其他 provider）就绪；密钥缺失或限流时该条计 `failed`，不中断批次。
2. **Day 3 抽取器 bug 修复** — 测试中发现 `event_extractor.py` 在 `model.invoke()` 返回 `None` 时崩溃（API Key 未配置场景），已增加 `if result is None` 检查。详见 Day 3 文档。
2. **逐条同步处理** — 逐条 LLM 调用，大批量时较慢；MVP 可接受，必要时引入并发（Day 3 处理器同样有此 TODO）。
3. **Prompt 固定** — importance_level 与 score 的对应关系由 Prompt 约束，LLM 可能偶尔不遵守；MVP 可接受，后续可在 schema 层加 validator。
4. **skipped_existing 恒为 0** — 当前实现中已分析事件不进入待处理列表，该字段预留但未实际计数。

---

## 8. 与 Day 6 的衔接

Day 6 一键演示链路为：`collect → extract → analyze → 展示`，本层的 `POST /api/jobs/analyze` 是其中最后一步处理环节。Day 5 前端的 `AnalysisCard` 在有分析数据后自动从降级占位切换为完整展示。Day 6 只需串联三个接口即可完成全链路演示。
