"""统计接口：GET /api/stats — Dashboard 仪表盘聚合数据。

纯只读聚合查询，不改业务逻辑、不加迁移、不动模型。用 SQLAlchemy func.count +
group_by 聚合 events / event_analysis / event_sources / raw_news 四张表。

异常隔离沿用项目约定：聚合查询本身不抛业务异常，DB 层错误由 FastAPI 统一处理。
"""

from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db, utcnow
from app.models.event import Event
from app.models.event_analysis import EventAnalysis
from app.models.event_source import EventSource
from app.models.raw_news import (
    EXTRACT_STATUS_FAILED,
    EXTRACT_STATUS_NOISE,
    EXTRACT_STATUS_PENDING,
    RawNews,
)
from app.schemas.stats import (
    LevelCount,
    SourceCount,
    StatsOut,
    TopEvent,
    TrendPoint,
    TypeCount,
)

router = APIRouter()

# 趋势窗口天数；近 N 天（含今天）按 created_at 日期分组
_TREND_DAYS = 14
# 重要事件流：仅 S·A 级，最多取前 N 条
_TOP_LIMIT = 8
_IMPORTANT_LEVELS = ("S", "A")


@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)) -> StatsOut:
    """仪表盘聚合统计。

    一次请求返回 totals / 类型分布 / 等级分布 / 14 天趋势 / 来源分布 / 重要事件流。
    等级分布把尚未生成分析的事件归为 ``"none"``；趋势补齐无事件日的零值，保证前端
    折线图横轴连续。top_events 仅取 S·A 级、按分数降序。totals 含 raw_news 各抽取
    状态计数（pending/noise/failed），供 Dashboard 观察流水线积压。
    """
    # ===== totals =====
    totals = {
        "events": db.scalar(select(func.count()).select_from(Event)) or 0,
        "analyzed": db.scalar(select(func.count()).select_from(EventAnalysis)) or 0,
        "sources": db.scalar(select(func.count()).select_from(EventSource)) or 0,
        "raw_news": db.scalar(select(func.count()).select_from(RawNews)) or 0,
        # raw_news 各抽取状态计数（验证流水线积压：pending 应随处理下降）
        "pending": db.scalar(
            select(func.count())
            .select_from(RawNews)
            .where(RawNews.extract_status == EXTRACT_STATUS_PENDING)
        )
        or 0,
        "noise": db.scalar(
            select(func.count())
            .select_from(RawNews)
            .where(RawNews.extract_status == EXTRACT_STATUS_NOISE)
        )
        or 0,
        "failed": db.scalar(
            select(func.count())
            .select_from(RawNews)
            .where(RawNews.extract_status == EXTRACT_STATUS_FAILED)
        )
        or 0,
    }

    # ===== 事件类型分布 =====
    type_rows = db.execute(
        select(Event.event_type, func.count()).group_by(Event.event_type)
    ).all()
    type_distribution = [TypeCount(type=t, count=c) for t, c in type_rows]

    # ===== 重要性等级分布（含未分析 → "none"）=====
    # 总事件数 - 已分析数 = 未分析数
    analyzed_total = totals["analyzed"]
    none_count = max(totals["events"] - analyzed_total, 0)
    level_rows = db.execute(
        select(EventAnalysis.importance_level, func.count()).group_by(
            EventAnalysis.importance_level
        )
    ).all()
    level_map: dict[str, int] = {lvl: c for lvl, c in level_rows}
    # 固定顺序 S/A/B/C，再补 none
    level_distribution = [
        LevelCount(level=lvl, count=level_map.get(lvl, 0))
        for lvl in ("S", "A", "B", "C")
    ]
    if none_count > 0:
        level_distribution.append(LevelCount(level="none", count=none_count))

    # ===== 近 N 天趋势（按 created_at 日期分组，补零）=====
    today = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=_TREND_DAYS - 1)
    trend_rows = db.execute(
        select(
            func.date(Event.created_at).label("d"),
            func.count(),
        )
        .where(Event.created_at >= start)
        .group_by(func.date(Event.created_at))
    ).all()
    trend_map: dict[str, int] = {str(d): c for d, c in trend_rows}
    trend: list[TrendPoint] = []
    for i in range(_TREND_DAYS):
        day = start + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        trend.append(TrendPoint(date=key, count=trend_map.get(key, 0)))

    # ===== 采集来源分布 =====
    source_rows = db.execute(
        select(RawNews.source, func.count()).group_by(RawNews.source)
    ).all()
    source_distribution = [SourceCount(source=s, count=c) for s, c in source_rows]

    # ===== 重要事件流（S·A 级，按分数降序）=====
    top_rows = db.scalars(
        select(Event)
        .join(EventAnalysis)
        .where(EventAnalysis.importance_level.in_(_IMPORTANT_LEVELS))
        .order_by(EventAnalysis.importance_score.desc(), Event.created_at.desc())
        .limit(_TOP_LIMIT)
    ).all()
    top_events = [
        TopEvent(
            id=e.id,
            event_id=e.event_id,
            event_title=e.event_title,
            event_type=e.event_type,
            importance_level=e.analysis.importance_level if e.analysis else None,
            importance_score=e.analysis.importance_score if e.analysis else None,
            created_at=e.created_at,
        )
        for e in top_rows
    ]

    return StatsOut(
        totals=totals,
        type_distribution=type_distribution,
        level_distribution=level_distribution,
        trend=trend,
        source_distribution=source_distribution,
        top_events=top_events,
    )
