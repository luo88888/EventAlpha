# Day 5：产品服务层实现说明

> 对应 MVP 一周计划 Day 5「产品服务层」。
>
> 技术栈：**FastAPI + SQLAlchemy（后端接口） / Next.js 15 + TypeScript + Tailwind v4（前端页面）**
>
> 日期：2026-06-25

---

## 1. 完成内容

Day 5 把事件卡片对外暴露：**后端补全列表筛选 / 详情 / 卡片三个接口 + 集成测试，前端从零搭建列表页与详情页（含分析卡片）**。四张表 Day 1 已建好，本层不动表结构、不加迁移。

### 1.1 后端新建/修改文件

| 文件 | 作用 |
|------|------|
| `backend/app/schemas/event.py` | 追加 `EventSourceOut` / `AnalysisOut` / `EventDetail` / `EventCard` |
| `backend/app/api/v1/events.py` | 扩展 `list_events` 筛选 + 新增 `GET /events/{id}`、`GET /events/{id}/card` |
| `backend/app/main.py` | 加 `CORSMiddleware`（允许 Next.js dev `localhost:3000`） |
| `backend/tests/conftest.py` | 内存 SQLite + 依赖注入 override `get_db`，与生产库隔离 |
| `backend/tests/integration/test_events_api.py` | 14 例集成测试 |

### 1.2 前端新建文件

| 文件 | 作用 |
|------|------|
| `frontend/lib/types.ts` `api.ts` | 对齐后端 schema 的 TS 类型 + fetch 客户端 |
| `frontend/app/page.tsx` | 事件列表页（根路径） |
| `frontend/app/events/[id]/page.tsx` | 事件详情页 |
| `frontend/app/{layout,loading,error,not-found}.tsx` | 根布局 + 加载/错误/404 兜底 |
| `frontend/app/events/[id]/not-found.tsx` | 详情 404 |
| `frontend/components/*.tsx` | FilterBar / EventListItem / Pagination / EventTypeTag / ImportanceBadge / AnalysisCard / CausalChain / FactorList / SourceList / EmptyAnalysis |
| `frontend/next.config.mjs` | rewrites 代理 `/api/**` → 后端 |

### 1.3 新增依赖

- 后端：无（复用 fastapi / sqlalchemy / pytest / httpx）。
- 前端：Next 15、React 19、Tailwind v4、TypeScript、ESLint。

---

## 2. 架构说明

### 2.1 后端数据流

```
GET /api/events          events [+INNER JOIN event_analysis（仅筛重要性时）]
GET /api/events/{id}     events ──┬─ sources → event_sources → raw_news（跨表来源）
                                  └─ analysis → event_analysis（一对一，可空）
GET /api/events/{id}/card  上面两表扁平合并，title←event_title，无分析降级
```

### 2.2 关键设计

- **路径参数用整型 `id`**：真正主键，FK 一致，主键查询最快，FastAPI `id: int` 自动 422。`event_id`（EVT_…）仅作响应字段。
- **importance 筛选 INNER JOIN，仅在传参时加**：筛时只回有分析且等级匹配的事件；不筛时返回全部（含无分析）。这是「筛时只回有分析、不筛时全回」的关键。
- **时间筛选用 `created_at`**（非空、按「最近」语义）；`event_time` 可空，不适合作最近事件筛选。
- **eager load 避免 N+1**：详情用 `selectinload(Event.sources).selectinload(EventSource.raw_news)` + `selectinload(Event.analysis)`，项目首次引入。
- **卡片手动组装**：跨表合并 + 字段重命名（`title`←`event_title`）+ 无分析降级，`from_attributes` 不适合，端点内手动构造 `EventCard`。
- **无分析降级是必经路径**：真实库 41 events / 0 event_analysis，详情与卡片接口对 `analysis is None` 全路径兜底（空数组 / None）。

### 2.3 前端数据流

```
浏览器 → Next dev(3000) ──rewrites──→ FastAPI(8000)/api
列表页：await searchParams → fetchEvents → EventListItem 列表 + FilterBar + Pagination
详情页：await params → fetchEventDetail（含 sources+analysis）→ 事件头 + AnalysisCard + SourceList
```

- **Server Component 默认**，`cache: "no-store"` 刷新即最新；筛选用原生 `<form method="get">` 改 URL searchParams 触发 Server 重渲染（纯 Server，无 `use client`）。
- **Next 15 坑**：`searchParams` / `params` 是 Promise，必须 `await`。
- **服务端 fetch 用绝对 URL**：Server Component 在 Node 端 fetch 相对路径会 `ERR_INVALID_URL`，故 `api.ts` 在服务端用 `process.env.BACKEND_URL` 绝对地址直连后端，客户端才走 `/api` 由 rewrites 代理。
- **详情页只用 `fetchEventDetail`**（已含 analysis），不调 `/card`，避免双请求。
- **Tailwind v4**：`globals.css` 单行 `@import "tailwindcss"`，无 config 文件，不自定义主题。

---

## 3. 接口说明

### 3.1 `GET /api/events`

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `event_type` | str | 无 | 按事件类型过滤 |
| `importance_level` | str | 无 | 按重要性 S/A/B/C（INNER JOIN，排除无分析） |
| `start_time` / `end_time` | datetime | 无 | 按 `created_at` 范围 |
| `limit` / `offset` | int | 50 / 0 | 分页 |

响应 `list[EventOut]`，按 `created_at` 倒序。

### 3.2 `GET /api/events/{id}`

响应 `EventDetail`：`EventOut` 全字段 + `sources: EventSourceOut[]`（source_name/title/url/source/published_at）+ `analysis: AnalysisOut | null`。事件不存在 → 404。

### 3.3 `GET /api/events/{id}/card`

响应 `EventCard`（计划第 6 节字段，扁平）：`event_id` / `title` / `event_type` / `summary` / `source_count` + 分析字段（无分析时 `importance_level`/`score=null`、各数组 `[]`、`risk_warning=null`）。事件不存在 → 404。

---

## 4. 验证结果

### 4.1 后端测试

```bash
cd backend
.venv/Scripts/python.exe -m pytest tests/integration/test_events_api.py -v
```

14 例全绿（列表筛选 6 + 详情 4 + 卡片 4），覆盖 INNER JOIN 排除、跨表来源映射、无分析降级、字段重命名、404。全量 22 passed（含 Day 3 去重单测 8 例）。

### 4.2 前端构建

```bash
cd frontend
npm run build   # 编译 + 类型检查通过，4 路由生成
npm run lint    # No warnings or errors
```

### 4.3 联调（后端 8000 + 前端 3000）

- 列表页渲染真实事件（41 条）；`?event_type=policy` 筛选返回 3 条。
- 详情页 `/events/1`：事件头 + 「暂未生成分析」降级占位 + 来源列表（真实库全无分析，验证降级路径）。
- `/events/99999` → 事件不存在 404 页。

---

## 5. 如何运行

```bash
# 后端
cd backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload   # :8000

# 前端
cd frontend
npm install
npm run dev                                                  # :3000
```

打开 `http://localhost:3000`。前端经 rewrites 代理调后端，同源无跨域。

---

## 6. 已知问题与后续

1. **真实库全无分析** — Day 4 推理分析层未做，详情/卡片当前全走降级占位；Day 4 完成后自然填充，前端无需改动。
2. **importance 筛选当前返回空** — 同上，有分析数据后即生效。
3. **CORS 源硬编码 `localhost:3000`** — MVP 先写死，后续可抽 config。
4. **分页无 total** — 用「本页满 limit 启发式显示下一页」，MVP 够用。
5. **`/card` 接口未被前端使用** — 详情页用 detail 接口已含 analysis；`fetchEventCard` 保留备用。
6. **`next lint` 将于 Next 16 废弃** — 后续迁移到 ESLint CLI。

---

## 7. 与 Day 4 / Day 6 的衔接

Day 4 推理分析层写入 `event_analysis`（与 `events` 一对一）后，Day 5 的详情页 `AnalysisCard` 与卡片接口自动从「无分析降级」切换为展示完整分析（重要性、影响行业/资产、因果链、风险提示），前端零改动。Day 6 一键演示链路 `collect → extract → analyze → 展示` 中，本层是「展示」环节。
