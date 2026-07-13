"""事件处理编排：读未处理 raw_news → 抽取 → 去重合并 → 写 events/event_sources。

数据流见 docs/Day3_事件处理层说明.md。核心函数 process_all(db) 是 Day 3 入口，
Day 6 一键演示链路 collect → extract → analyze 的中间环节。

已处理判定：用 raw_news.extract_status 字段，只取 pending（待处理）。三种结局落库标记：
- 抽取失败(extract_event 返回 None)→ extract_status='failed'，永久跳过（用户已确认不重试）
- LLM 判为噪声(event_type=='other')→ extract_status='noise'，永久跳过
- 成功抽取并写 event_sources → extract_status='extracted'
运维兜底：如需重处理单条，手动 `UPDATE raw_news SET extract_status='pending' WHERE id=<X>`。
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_source import EventSource
from app.models.raw_news import (
    EXTRACT_STATUS_EXTRACTED,
    EXTRACT_STATUS_FAILED,
    EXTRACT_STATUS_NOISE,
    EXTRACT_STATUS_PENDING,
    RawNews,
)
from app.processors.event_dedup import MergeCandidate, find_mergeable
from app.processors.event_extractor import extract_event
from app.schemas.event import ExtractResult

logger = logging.getLogger(__name__)

# 合并候选池：取近 N 天既有事件作为可合并目标（避免与太久远事件误并）
_MERGE_LOOKBACK_DAYS = 7
# 视为非事件的类型（LLM 判定为噪声时跳过，标 noise 永久跳过）
_NOISE_TYPE = "other"

# TODO: 优先级 2，实现并发处理，提高抽取效率

def _load_unprocessed_news(db: Session) -> list[RawNews]:
    """查询待处理的原始新闻（extract_status == pending）。

    用状态字段判定而非反查 event_sources：噪声/失败/已抽取的新闻都已落库标记，
    不会被重复取出，避免反复调 LLM。按 collected_at 升序处理（先采先处理）。
    """
    stmt = (
        select(RawNews)
        .where(RawNews.extract_status == EXTRACT_STATUS_PENDING)
        .order_by(RawNews.collected_at)
    )
    return list(db.scalars(stmt).all())


def _load_merge_candidates(
    db: Session, lookback_days: int = _MERGE_LOOKBACK_DAYS
) -> list[MergeCandidate]:
    """加载近 N 天既有事件作为合并候选池。"""
    since = datetime.utcnow() - timedelta(days=lookback_days)
    stmt = select(Event).where(Event.created_at >= since)
    return [
        MergeCandidate(id=e.id, event_title=e.event_title, event_type=e.event_type)
        for e in db.scalars(stmt).all()
    ]


def _next_event_id(db: Session) -> str:
    """生成当日展示码 EVT_YYYYMMDD_NNN：当日已有最大序号 +1。"""
    today = datetime.utcnow()
    prefix = f"EVT_{today.strftime('%Y%m%d')}_"
    # 取当日同前缀的最大序号（按字典序也等价于数值序，因为 NNN 定宽）
    stmt = select(func.max(Event.event_id)).where(Event.event_id.like(f"{prefix}%"))
    max_id = db.scalar(stmt)
    if max_id:
        try:
            seq = int(max_id[len(prefix):]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:03d}"


def process_all(db: Session) -> ExtractResult:
    """处理一批未处理新闻：抽取事件、去重合并、写库。

    Args:
        db: 数据库会话（由调用方负责提交/关闭；本函数内部 commit）。

    Returns:
        ExtractResult：本轮处理统计。
    """
    news_list = _load_unprocessed_news(db)
    if not news_list:
        logger.info("没有待处理的原始新闻")
        return ExtractResult()

    candidates = _load_merge_candidates(db)
    # 本批次已生成事件也加入候选池，使同批次内的重复新闻互相合并
    batch_new: list[MergeCandidate] = []

    processed = 0
    new_events = 0
    merged = 0
    skipped_noise = 0
    failed = 0

    for news in news_list:
        extracted = extract_event(news)
        if extracted is None:
            # 抽取失败：标记 failed 永久跳过（用户已确认不重试）
            news.extract_status = EXTRACT_STATUS_FAILED
            failed += 1
            logger.warning("抽取失败标记 news_id=%s → extract_status=failed", news.id)
            continue

        # LLM 判定为非事件：标记 noise 永久跳过，不建事件、不写关联
        if extracted.event_type == _NOISE_TYPE:
            news.extract_status = EXTRACT_STATUS_NOISE
            skipped_noise += 1
            continue

        processed += 1
        pool = candidates + batch_new
        target = find_mergeable(extracted.event_title, extracted.event_type, pool)

        if target is not None:
            # 合并：追加 event_sources，source_count +1
            _add_source(db, event_pk=target.id, news=news)
            merged += 1
            logger.info("合并事件 news_id=%s -> event_id_pk=%s", news.id, target.id)
        else:
            # 新建事件
            event = Event(
                event_id=_next_event_id(db),
                event_title=extracted.event_title,
                event_type=extracted.event_type,
                event_subject=extracted.event_subject,
                event_time=extracted.event_time,
                summary=extracted.summary,
                source_count=1,
                status="new",
            )
            db.add(event)
            db.flush()  # 拿到 event.id 再写关联
            _add_source(db, event_pk=event.id, news=news)
            batch_new.append(
                MergeCandidate(
                    id=event.id,
                    event_title=event.event_title,
                    event_type=event.event_type,
                )
            )
            new_events += 1
            logger.info("新建事件 event_id=%s news_id=%s", event.event_id, news.id)

    try:
        db.commit()
    except Exception as e:  # noqa: BLE001
        logger.error("事件批次提交失败: %s", e)
        db.rollback()
        return ExtractResult(
            processed=0, new_events=0, merged=0,
            skipped_noise=skipped_noise, failed=failed,
        )

    logger.info(
        "事件处理完成: processed=%d, new_events=%d, merged=%d, skipped_noise=%d, failed=%d",
        processed, new_events, merged, skipped_noise, failed,
    )
    return ExtractResult(
        processed=processed,
        new_events=new_events,
        merged=merged,
        skipped_noise=skipped_noise,
        failed=failed,
    )


def _add_source(db: Session, event_pk: int, news: RawNews) -> None:
    """写入一条 event_sources 关联，并把新闻标记为 extracted。

    合并路径与新建路径都走这里，保证「写关联」与「标 extracted」原子一致。
    """
    news.extract_status = EXTRACT_STATUS_EXTRACTED
    db.add(
        EventSource(
            event_id=event_pk,
            raw_news_id=news.id,
            source_name=news.source,
        )
    )
