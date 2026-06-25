"""EventAlpha FastAPI 入口。

挂载路由、启动时确保数据库表存在、启动定时任务、健康检查。
所有命令从 backend/ 目录运行：uv run uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from app.core.logging_config import setup_logging

setup_logging()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.collect import router as collect_router
from app.api.v1.events import router as events_router
from app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时建表 + 启动定时任务，shutdown 时停止定时任务。"""
    from app.scheduler import start_scheduler, stop_scheduler

    Base.metadata.create_all(bind=engine)
    stop_event = start_scheduler()
    yield
    stop_scheduler(stop_event)


app = FastAPI(
    title="EventAlpha",
    description="热点事件驱动投资研究 MVP",
    version="0.1.0",
    lifespan=lifespan,
)

# 跨域：允许 Next.js dev（localhost:3000）访问 API。MVP 先硬编码源，后续可抽 config。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# 挂载 v1 路由
app.include_router(collect_router, prefix="/api", tags=["jobs"])
app.include_router(events_router, prefix="/api", tags=["events"])
