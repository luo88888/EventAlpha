"""数据库基础设施：引擎、会话、Base、依赖注入、SQLite 外键强制。

同步引擎（MVP 批处理流水线，无高并发 HTTP 需求；Alembic autogenerate 在同步引擎下最简单）。
SQLite 默认不强制外键，需在 connect 事件里开启 PRAGMA foreign_keys=ON。
时间采用 UTC naive 约定（SQLite 无原生 datetime 类型，func.now() 会写本地时间，故用 Python default）。
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from utils.config_handler import load_database_config

settings = load_database_config()

engine = create_engine(
    settings.url,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """SQLite 默认关闭外键约束，连接建立时开启，使 ondelete=CASCADE 生效。"""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """所有 ORM 模型的声明基类。"""


def utcnow() -> datetime:
    """当前 UTC 时间（naive），供 created_at/collected_at 的 Python default 使用。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖：提供一个会话并在请求结束后关闭。

    当前数据层不依赖 FastAPI，先定义好供 Day 2 产品服务层直接复用。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
