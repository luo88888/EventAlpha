"""RSS 采集器：拉取新闻源、去重、写入 raw_news。

去重策略：
- primary: content_hash (SHA-256 of title + url)，UNIQUE 约束
- fallback: URL 索引查询（content_hash 未命中时按 url 再查一次）

采集的 RSS 源列表在 RSS_SOURCES 中配置，可按需增减。
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.raw_news import RawNews

logger = logging.getLogger(__name__)

# ── RSS 源配置 ──────────────────────────────────────────────
# 每个源：name（写入 source 字段）、url（RSS 地址）
RSS_SOURCES: list[dict[str, str]] = [
    {
        "name": "reuters",
        "url": "https://feeds.reuters.com/reuters/topNews",
    },
    {
        "name": "bbc",
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
    },
    {
        "name": "cnbc",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
    },
    {
        "name": "aljazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
    },
]

# HTTP 请求超时（秒）
HTTP_TIMEOUT = 30


@dataclass
class CollectStats:
    """单个源的采集统计。"""

    source: str
    fetched: int = 0
    new: int = 0
    skipped: int = 0


def _compute_hash(title: str, url: str) -> str:
    """根据标题 + URL 生成 SHA-256 内容哈希（主去重键）。"""
    raw = f"{title.strip()}|{url.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _parse_datetime(entry) -> datetime | None:
    """尝试从 feedparser entry 提取发布时间，转为 UTC naive datetime。"""
    for field in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, field, None)
        if parsed:
            try:
                from time import mktime

                return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc).replace(
                    tzinfo=None
                )
            except (ValueError, OverflowError, OSError):
                continue
    return None


def _fetch_feed(url: str) -> feedparser.FeedParserDict:
    """拉取并解析 RSS feed。"""
    resp = httpx.get(url, timeout=HTTP_TIMEOUT, follow_redirects=True)
    resp.raise_for_status()
    return feedparser.parse(resp.text)


def collect_source(db: Session, source_cfg: dict[str, str]) -> CollectStats:
    """采集单个 RSS 源，去重后写入 raw_news。

    Args:
        db: 数据库会话
        source_cfg: {"name": "reuters", "url": "https://..."}

    Returns:
        CollectStats: 采集统计
    """
    name = source_cfg["name"]
    url = source_cfg["url"]
    stats = CollectStats(source=name)

    try:
        feed = _fetch_feed(url)
    except Exception as e:
        logger.error("采集 %s 失败: %s", name, e)
        return stats

    entries = feed.get("entries", [])
    stats.fetched = len(entries)

    for entry in entries:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            stats.skipped += 1
            continue

        content_hash = _compute_hash(title, link)

        # 主去重：content_hash
        exists = db.execute(
            select(RawNews.id).where(RawNews.content_hash == content_hash)
        ).first()
        if exists:
            stats.skipped += 1
            continue

        # 备用去重：url
        url_exists = db.execute(
            select(RawNews.id).where(RawNews.url == link)
        ).first()
        if url_exists:
            stats.skipped += 1
            continue

        summary = entry.get("summary") or entry.get("description") or None
        # feedparser 的 summary 可能含 HTML 标签，简单去标签
        if summary:
            import re

            summary = re.sub(r"<[^>]+>", "", summary).strip()[:2000] or None

        news = RawNews(
            source=name,
            title=title[:512],
            summary=summary,
            url=link[:1024],
            content_hash=content_hash,
            published_at=_parse_datetime(entry),
        )
        db.add(news)
        stats.new += 1

    db.commit()
    logger.info(
        "采集 %s: fetched=%d, new=%d, skipped=%d",
        name,
        stats.fetched,
        stats.new,
        stats.skipped,
    )
    return stats


def collect_all(db: Session, sources: list[dict[str, str]] | None = None) -> list[CollectStats]:
    """采集所有配置的 RSS 源。

    Args:
        db: 数据库会话
        sources: 自定义源列表，None 则用默认 RSS_SOURCES

    Returns:
        每个源的采集统计列表
    """
    if sources is None:
        sources = RSS_SOURCES
    return [collect_source(db, src) for src in sources]
