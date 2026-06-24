"""events：结构化事件表（事件处理层产物）。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.event_analysis import EventAnalysis
    from app.models.event_source import EventSource


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 展示码 EVT_20260624_001，业务唯一键；真正主键用整型 id（FK 指向 id 而非此列）
    event_id: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    event_title: Mapped[str] = mapped_column(String(512), nullable=False)
    # 字符串而非 Enum，便于扩展事件类型且便于迁移
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    event_subject: Mapped[str | None] = mapped_column(String(256), nullable=True)
    event_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="new", server_default="new", index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    sources: Mapped[list["EventSource"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )
    # 一对一：一个事件最多一份分析
    analysis: Mapped["EventAnalysis | None"] = relationship(
        back_populates="event", uselist=False, cascade="all, delete-orphan"
    )
