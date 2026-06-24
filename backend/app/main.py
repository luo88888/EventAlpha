"""EventAlpha FastAPI 入口。

挂载路由、启动时确保数据库表存在、健康检查。
所有命令从 backend/ 目录运行：uv run uvicorn app.main:app --reload
"""

from __future__ import annotations

from app.core.logging_config import setup_logging

setup_logging()

from fastapi import FastAPI

from app.api.v1.collect import router as collect_router
from app.api.v1.events import router as events_router
from app.core.database import Base, engine

app = FastAPI(
    title="EventAlpha",
    description="热点事件驱动投资研究 MVP",
    version="0.1.0",
)


@app.on_event("startup")
def _ensure_tables() -> None:
    """启动时如果表不存在则创建（MVP 简化，正式环境用 alembic）。"""
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# 挂载 v1 路由
app.include_router(collect_router, prefix="/api", tags=["jobs"])
app.include_router(events_router, prefix="/api", tags=["events"])
