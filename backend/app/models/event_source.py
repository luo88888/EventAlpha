"""event_sources：事件与原始新闻的多源关联表。

带元数据（source_name、created_at），故用完整模型而非裸 Table；
(event_id, raw_news_id) 唯一约束防止同一新闻重复归属同一事件。
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.event import Event
    from app.models.raw_news import RawNews


class EventSource(Base):
    __tablename__ = "event_sources"
    __table_args__ = (
        UniqueConstraint("event_id", "raw_news_id", name="uq_event_source_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # FK 指向整型 id（非展示码 event_id），连接更便宜且对 Postgres 友好
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_news_id: Mapped[int] = mapped_column(
        ForeignKey("raw_news.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    event: Mapped["Event"] = relationship(back_populates="sources")
    raw_news: Mapped["RawNews"] = relationship(back_populates="event_sources")
