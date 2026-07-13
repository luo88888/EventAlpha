# EventAlpha

> 热点事件驱动投资研究 MVP —— 从 RSS 采集 → 事件抽取 → 影响分析 → 可视化展示的自动化投研助手。

EventAlpha 定时抓取财经新闻,用大模型把原始新闻结构化为「事件」,再做投资影响分析(重要性评分、影响行业、因果传导链、风险提示),最后通过 Web 控制台和 API 暴露给用户。核心价值:把「人看新闻 → 人判断影响」自动化为「系统采集 → 系统抽取 → 系统分析 → 人查阅可解释的事件卡片」。

![architecture](docs/系统架构图.md)

---

## ✨ 核心特性

- 📡 **自动采集**:5 个中文财经 RSS 源(36kr / 华尔街见闻 / 财新 / 新浪财经 / 东方财富),内容哈希去重,每 30 分钟定时跑完整流水线。
- ⚙️ **事件抽取**:LLM 结构化抽取事件标题/类型/主体/时间/摘要,字符 bigram 覆盖度去重合并,`extract_status` 状态机永久跳过噪声与失败新闻。
- 🧠 **影响分析**:并发 LLM 分析,输出重要性评分(S/A/B/C)、影响行业与资产、因果传导链、正负面因素、风险提示;429 限流指数退避重试。
- 🖥️ **Dashboard 控制台**:暗色金融终端风格,KPI 卡片 + 类型/等级/趋势图表 + 重要事件流。
- 🔐 **用户登录**:bcrypt + JWT httpOnly Cookie,注册/登录/登出,现有查询 API 保持开放。
- 🔌 **REST API**:事件列表/详情/卡片、Dashboard 聚合统计、手动触发采集/抽取/分析。
- 🧪 **测试覆盖**:后端 57 用例(单测 + 集成),前端 TypeScript + ESLint 零错误。

---

## 🛠️ 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.12 · FastAPI(同步)· SQLAlchemy 2.0 · Alembic · Pydantic v2 |
| 数据库 | SQLite(单文件,可平滑迁 PostgreSQL) |
| LLM | LangChain 1.x 统一封装,支持 DeepSeek / 通义千问 / OpenAI / 小米 MiMo |
| 鉴权 | bcrypt 密码哈希 + PyJWT(HS256)+ httpOnly Cookie |
| 前端 | Next.js 15 App Router · React 19 · TypeScript · Tailwind v4 · recharts · framer-motion |
| 测试 | pytest · ruff · next lint |

---

## 🚀 快速开始

### 环境要求

- Python ≥ 3.12
- Node.js(支持 Next.js 15)
- [uv](https://github.com/astral-sh/uv)(Python 包管理)

### 后端

```bash
cd backend

# 1. 安装依赖
uv pip install -e ".[dev]" --python .venv/Scripts/python.exe

# 2. 配置密钥:复制模板并填入
cp .env_example .env
#   编辑 .env,填入至少一个 LLM API Key 和 SECRET_KEY
#   生成 SECRET_KEY:python -c "import secrets;print(secrets.token_urlsafe(48))"

# 3. 应用数据库迁移
.venv/Scripts/python.exe -m alembic upgrade head

# 4. 启动服务(localhost:8000)
.venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev    # http://localhost:3000,默认代理到 http://localhost:8000
```

打开 http://localhost:3000 即可看到 Dashboard 控制台。访问 `/register` 注册账号,`/login` 登录。

### LLM 提供方

默认用小米 MiMo(`config/llm.yaml`:`xiaomi` / `mimo-v2.5-pro`)。在 `.env` 填对应 API Key 即可切换:

| provider | 环境变量 |
|---|---|
| `xiaomi`(默认) | `XIAOMI_API_KEY` |
| `deepseek` | `DEEPSEEK_API_KEY` |
| `qwen` | `DASHSCOPE_API_KEY` |
| `openai` | `OPENAI_API_KEY` |

---

## 📐 架构速览

四层流水线 + 服务层,上层产物表是下层输入:

```
📡 采集层 collectors/    RSS×5 → 去重 → raw_news
        ↓
⚙️ 处理层 processors/    raw_news → LLM 抽取 → bigram 合并 → events/event_sources
        ↓
🧠 分析层 analysis/      events → 并发 LLM → event_analysis(1:1)
        ↓
🖥️ 服务层 api/v1/ + frontend/  事件列表/详情/卡片/统计 + Next.js 前端 + 用户登录
```

定时任务 `scheduler.py` 每 30 分钟串行跑 `collect → extract → analyze`(单步失败不阻塞后续);手动触发 API 亦可用。

完整的架构图(含数据流、ER 图、API 路由、鉴权链路、LLM 工厂)见 [docs/系统架构图.md](docs/系统架构图.md)。

---

## 🔌 API 一览

所有路由挂 `/api` 前缀,CORS 允许 `localhost:3000`。

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/health` | 健康检查 | 开放 |
| GET | `/api/events` | 事件列表(筛选 + 分页) | 开放 |
| GET | `/api/events/{id}` | 事件详情(含来源 + 分析) | 开放 |
| GET | `/api/events/{id}/card` | 事件卡片(扁平视图) | 开放 |
| GET | `/api/stats` | Dashboard 聚合统计 | 开放 |
| POST | `/api/jobs/collect` | 手动触发 RSS 采集 | 开放 |
| POST | `/api/jobs/extract` | 手动触发事件抽取 | 开放 |
| POST | `/api/jobs/analyze` | 手动触发事件分析 | 开放 |
| POST | `/api/auth/register` | 注册(成功即自动登录) | 开放 |
| POST | `/api/auth/login` | 登录 | 开放 |
| POST | `/api/auth/logout` | 登出 | 开放 |
| GET | `/api/auth/me` | 当前登录用户 | **需登录** |

> 鉴权范围:仅 `/api/auth/me` 需登录。事件/统计/采集 API 保持开放,符合「仅新增登录能力」的 MVP 决策。

手动触发一次完整流水线:

```bash
curl -X POST http://localhost:8000/api/jobs/collect
curl -X POST http://localhost:8000/api/jobs/extract
curl -X POST http://localhost:8000/api/jobs/analyze
```

---

## 🗄️ 数据库

SQLite,5 张表:

| 表 | 职责 |
|---|---|
| `raw_news` | 原始新闻(`content_hash` 唯一去重,`extract_status` 状态字段) |
| `events` | 结构化事件(展示码 `EVT_YYYYMMDD_NNN`,整型 `id` 为主键) |
| `event_sources` | 事件↔新闻多源关联(`(event_id, raw_news_id)` 组合唯一) |
| `event_analysis` | 投资影响分析(与 events 一对一,`importance_score` CHECK 1-5) |
| `users` | 用户(`username` 唯一,`password_hash` bcrypt) |

ER 关系图见 [docs/系统架构图.md](docs/系统架构图.md#3-数据库-er-关系mermaid)。

---

## 🧪 测试

```bash
cd backend

# 全部测试
.venv/Scripts/python.exe -m pytest

# 仅鉴权
.venv/Scripts/python.exe -m pytest tests/integration/test_auth_api.py -v

# Lint
.venv/Scripts/python.exe -m ruff check .
```

前端:

```bash
cd frontend
npx tsc --noEmit    # 类型检查
npm run lint        # ESLint
```

---

## 📂 目录结构

```
EventAlpha/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口(lifespan + 路由挂载)
│   │   ├── scheduler.py         # 定时流水线(每 30 分钟)
│   │   ├── core/                # database / logging_config / security
│   │   ├── api/                 # deps.py + v1/(events/stats/collect/auth)
│   │   ├── collectors/          # RSS 采集
│   │   ├── processors/          # 事件抽取 + 去重合并
│   │   ├── analysis/            # 投资影响分析(并发)
│   │   ├── services/llm/        # LLM 工厂(四方 provider)
│   │   ├── models/              # 5 个 ORM 模型
│   │   └── schemas/             # Pydantic 模型
│   ├── config/                  # YAML 配置 + prompts/ 模板
│   ├── alembic/                 # 数据库迁移
│   ├── tests/                   # unit + integration
│   └── .env_example             # 密钥模板
├── frontend/
│   ├── app/                     # layout + Dashboard + events + login/register
│   ├── components/              # ui/ + charts/ + 顶层组件
│   ├── lib/                     # api.ts / types.ts / constants.tsx / utils.ts
│   └── next.config.mjs          # rewrites 代理 /api → 后端
└── docs/
    ├── 系统功能说明.md           # 18 节完整功能说明
    └── 系统架构图.md             # ASCII + Mermaid 架构图
```

---

## 📖 更多文档

- [docs/系统功能说明.md](docs/系统功能说明.md) —— 18 节完整功能说明(定位、四层流水线、API、鉴权、前端、数据库、配置、测试、部署、设计取舍)
- [docs/系统架构图.md](docs/系统架构图.md) —— 总体架构、数据流、ER 图、API 路由、鉴权链路、LLM 工厂(ASCII + Mermaid)
- [CLAUDE.md](CLAUDE.md) —— 给 AI 助手的代码库指引(运行目录约定、常用命令、架构细节)
- [docs/EventAlpha_MVP一周项目计划.md](docs/EventAlpha_MVP一周项目计划.md) —— MVP 一周项目计划

---

## ⚠️ 合规提示

EventAlpha 仅供事件研究与学习,**不构成任何投资建议**。系统输出的事件分析(重要性评分、影响行业、因果链等)由 LLM 生成,可能存在偏差或错误,请独立判断。

---

## 📄 许可证

本项目为 MVP 原型,用于学习与研究目的。
