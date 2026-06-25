# Day 6：并发优化与小米 API 集成

> 对应 MVP 一周计划收尾阶段：分析层性能优化 + 多供应商扩展 + 定时任务。
>
> 技术栈：**ThreadPoolExecutor 并发 / 小米 MiMo API / FastAPI lifespan 定时任务**
>
> 日期：2026-06-26

---

## 1. 完成内容

Day 6 聚焦三个问题：分析层限流导致大量失败、缺少小米 API 支持、采集需手动触发。

### 1.1 分析层并发 + 限流重试

| 文件 | 改动 |
|------|------|
| `backend/app/analysis/event_analyzer.py` | 新增限流重试：检测 429/rate limit 错误，指数退避（2s→4s→8s），最多 3 次 |
| `backend/app/analysis/analysis_processor.py` | 串行改并发：`ThreadPoolExecutor` 并行调用 LLM，`_MAX_WORKERS` 控制并发度 |

### 1.2 小米 MiMo API 供应商

| 文件 | 改动 |
|------|------|
| `backend/app/services/llm/providers.py` | 新增 `_build_xiaomi()`：OpenAI 兼容，base_url `https://api.xiaomimimo.com/v1`，从 `XIAOMI_API_KEY` 读 key |
| `backend/config/llm.yaml` | 默认切换为 `default_provider: xiaomi` / `default_model: mimo-v2.5-pro` |
| `backend/.env_example` | 新增 `XIAOMI_API_KEY=` |

### 1.3 定时任务

| 文件 | 改动 |
|------|------|
| `backend/app/scheduler.py` | **新建**：后台线程，每 30 分钟自动执行 采集→抽取→分析 流水线 |
| `backend/app/main.py` | `on_event("startup")` 改为 `lifespan` 上下文管理器，启动/停止定时任务 |

### 1.4 文档更新

| 文件 | 改动 |
|------|------|
| `CLAUDE.md` | 补充前端命令、Testing 章节、Key Files 表、小米供应商、定时任务 |
| `backend/.env_example` | 新增 `XIAOMI_API_KEY` |

---

## 2. 并发性能测试（小米 mimo-v2.5-pro）

85 个事件，全部重新分析，0 失败，0 限流。

| 并发数 | 耗时 | 吞吐 | 提速 | 失败 |
|--------|------|------|------|------|
| 1（串行 + 1s 间隔） | ~480s | 0.17 事件/s | 基准 | 0 |
| 5 | 131s | 0.65 事件/s | 3.7x | 0 |
| 10 | 68s | 1.25 事件/s | 7x | 0 |
| 50 | 21s | 4.0 事件/s | 23x | 0 |
| 200 | 13s | 6.5 事件/s | 37x | 0 |

结论：
- 小米 API **无限流**，200 并发仍然 0 个 429 错误
- 瓶颈在单条请求的 LLM 推理时间（~3-7s/条），50 并发已接近极限
- 最终选择 `_MAX_WORKERS = 50` 作为默认值（性价比最高）

---

## 3. DeepSeek vs 小米 API 对比

同一 50 个事件，串行模式：

| 指标 | DeepSeek deepseek-chat | 小米 mimo-v2.5-pro |
|------|------------------------|-------------------|
| 成功 | 26/50 | 50/50 |
| 限流次数 | 35 次 | 0 次 |
| 失败次数 | 18 次 | 0 次 |
| 模型推理 | 快（~1-3s） | 较慢（~3-7s，含推理） |

结论：DeepSeek 限流严格（免费额度 QPS 低），小米按量付费无限流，适合批量分析场景。

---

## 4. 定时任务架构

```
FastAPI lifespan
    │
    ├── startup
    │   ├── Base.metadata.create_all()  # 建表
    │   └── start_scheduler()           # 启动后台线程
    │       └── 首次延迟 10s → 执行流水线 → sleep 30min → 循环
    │
    └── shutdown
        └── stop_scheduler()            # Event 通知线程退出
```

流水线步骤（串行，单步失败不阻塞后续）：
1. `collect_all(db)` — RSS 采集
2. `process_all(db)` — LLM 事件抽取 + 去重
3. `analyze_all(db)` — LLM 并发分析

手动触发 API 仍然可用（`POST /api/jobs/collect` / `extract` / `analyze`）。

---

## 5. 当前系统完整状态

| 层 | 状态 | 说明 |
|----|------|------|
| 采集层 | ✅ | 5 个 RSS 源，content_hash 去重，定时自动采集 |
| 处理层 | ✅ | LLM 抽取事件 + bigram 覆盖度去重 |
| 分析层 | ✅ | 85/85 事件有分析，并发 50，小米 API 无限流 |
| API 层 | ✅ | 7 个端点 + 定时任务自动运行 |
| 前端 | ✅ | 列表页 + 详情页 + 筛选分页 + 分析卡片 |
