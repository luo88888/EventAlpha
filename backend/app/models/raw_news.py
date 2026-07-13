"""raw_news：原始新闻表（数据采集层产物）。

extract_status 标记抽取处理状态（处理层据此跳过已处理/噪声/失败新闻）：
- pending   待处理（新采集 / 存量未处理）
- extracted 已成功抽取并写入 event_sources
- noise     LLM 判定为非事件(other)，永久跳过
- failed    LLM 抽取失败/异常，永久跳过
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.event_source import EventSource

# 抽取处理状态常量（取值集合由应用层保证，不加 DB CHECK 约束，与 events.status 一致）
EXTRACT_STATUS_PENDING = "pending"
EXTRACT_STATUS_EXTRACTED = "extracted"
EXTRACT_STATUS_NOISE = "noise"
EXTRACT_STATUS_FAILED = "failed"


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
    # 抽取处理状态：处理层 _load_unprocessed_news 只取 pending；噪声/失败/已抽取永久跳过
    # Python default + server_default 双设，覆盖 ORM INSERT 与 raw SQL 两条路径
    extract_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=EXTRACT_STATUS_PENDING,
        server_default=EXTRACT_STATUS_PENDING,
        index=True,
    )

    event_sources: Mapped[list["EventSource"]] = relationship(
        back_populates="raw_news", cascade="all, delete-orphan"
    )
