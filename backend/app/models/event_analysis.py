"""event_analysis：事件投资影响分析表（推理分析层产物，与 events 一对一）。

JSON 数组字段用 SQLAlchemy 便携 JSON 类型（SQLite 存 TEXT，PostgreSQL 存 json），
不使用 PG 专属 JSONB，保证可迁移。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.event import Event


class EventAnalysis(Base):
    __tablename__ = "event_analysis"
    __table_args__ = (
        # 可移植检查约束，随 CREATE TABLE 生成，批模式重建表时保留
        CheckConstraint("importance_score BETWEEN 1 AND 5", name="ck_importance_score_1_5"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # FK 上加 unique 在 DB 层强制"一事件一分析"
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    importance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    importance_level: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    affected_industries: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    affected_assets: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    causal_chain: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    positive_factors: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    negative_factors: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    risk_warning: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    event: Mapped["Event"] = relationship(back_populates="analysis")
