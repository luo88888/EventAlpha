"""raw_news：原始新闻表（数据采集层产物）。"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.event_source import EventSource


class RawNews(Base):
    __tablename__ = "raw_news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 同一文章可能经多个 URL 联合分发，url 不设 unique，仅普通索引便于按链接去重
    url: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    # 主去重键：内容哈希（SHA-256 hex = 64 字符），唯一
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)

    event_sources: Mapped[list["EventSource"]] = relationship(
        back_populates="raw_news", cascade="all, delete-orphan"
    )
