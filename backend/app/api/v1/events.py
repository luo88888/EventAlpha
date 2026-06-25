"""事件接口：

- GET /api/events：事件列表（支持 event_type / importance_level / 时间范围筛选，
  offset+limit 分页，按 created_at 倒序）。
- GET /api/events/{id}：事件详情（含来源列表与分析块）。
- GET /api/events/{id}/card：事件卡片 JSON（计划第 6 节字段，无分析时降级）。
- POST /api/jobs/extract：手动触发一次事件抽取处理。
- POST /api/jobs/analyze：手动触发一次事件分析处理。
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.analysis.analysis_processor import analyze_all
from app.core.database import get_db
from app.models.event import Event
from app.models.event_analysis import EventAnalysis
from app.models.event_source import EventSource
from app.processors.event_processor import process_all
from app.schemas.event import (
    AnalysisOut,
    AnalyzeResponse,
    EventCard,
    EventDetail,
    EventOut,
    EventSourceOut,
    ExtractResponse,
)

router = APIRouter()


@router.get("/events", response_model=list[EventOut])
def list_events(
    event_type: str | None = Query(default=None, description="按事件类型过滤"),
    importance_level: str | None = Query(default=None, description="按重要性等级过滤 S/A/B/C"),
    start_time: datetime | None = Query(default=None, description="起始时间（按 created_at）"),
    end_time: datetime | None = Query(default=None, description="结束时间（按 created_at）"),
    limit: int = Query(default=50, ge=1, le=200, description="返回条数上限"),
    offset: int = Query(default=0, ge=0, description="偏移量，简单分页"),
    db: Session = Depends(get_db),
) -> list[Event]:
    """事件列表。

    按 created_at 倒序返回。支持按 event_type、importance_level、时间范围筛选。
    importance_level 在 event_analysis 表上，筛选时用 INNER JOIN——只返回已生成
    分析且等级匹配的事件；不筛时返回全部（含尚未分析的事件）。MVP 用 offset/limit
    分页，不含游标与 total。
    """
    stmt = select(Event)
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    if importance_level:
        stmt = stmt.join(EventAnalysis).where(
            EventAnalysis.importance_level == importance_level
        )
    if start_time:
        stmt = stmt.where(Event.created_at >= start_time)
    if end_time:
        stmt = stmt.where(Event.created_at <= end_time)
    stmt = stmt.order_by(Event.created_at.desc()).offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/events/{id}", response_model=EventDetail)
def get_event_detail(id: int, db: Session = Depends(get_db)) -> EventDetail:
    """事件详情：主信息 + 来源列表（EventSource→RawNews）+ 分析块。

    selectinload 预加载 sources→raw_news 与 analysis，避免 N+1。来源字段跨表
    （source_name 在 event_sources，title/url/source/published_at 在 raw_news），
    手动映射为 EventSourceOut。事件不存在返回 404。
    """
    stmt = (
        select(Event)
        .options(
            selectinload(Event.sources).selectinload(EventSource.raw_news),
            selectinload(Event.analysis),
        )
        .where(Event.id == id)
    )
    event = db.scalars(stmt).first()
    if event is None:
        raise HTTPException(status_code=404, detail="事件不存在")

    sources_out = [
        EventSourceOut(
            source_name=es.source_name,
            title=es.raw_news.title,
            url=es.raw_news.url,
            source=es.raw_news.source,
            published_at=es.raw_news.published_at,
        )
        for es in event.sources
    ]
    analysis_out = AnalysisOut.model_validate(event.analysis) if event.analysis else None
    return EventDetail(
        id=event.id,
        event_id=event.event_id,
        event_title=event.event_title,
        event_type=event.event_type,
        event_subject=event.event_subject,
        event_time=event.event_time,
        summary=event.summary,
        source_count=event.source_count,
        status=event.status,
        created_at=event.created_at,
        sources=sources_out,
        analysis=analysis_out,
    )


@router.get("/events/{id}/card", response_model=EventCard)
def get_event_card(id: int, db: Session = Depends(get_db)) -> EventCard:
    """事件卡片：计划第 6 节字段，跨表扁平视图。

    基础字段来自 events（卡片用 title，由 event_title 映射），分析字段来自
    event_analysis。事件尚未分析时分析字段降级为 None / 空数组。事件不存在
    返回 404。
    """
    stmt = (
        select(Event)
        .options(selectinload(Event.analysis))
        .where(Event.id == id)
    )
    event = db.scalars(stmt).first()
    if event is None:
        raise HTTPException(status_code=404, detail="事件不存在")

    a = event.analysis
    return EventCard(
        event_id=event.event_id,
        title=event.event_title,
        event_type=event.event_type,
        summary=event.summary,
        source_count=event.source_count,
        importance_level=a.importance_level if a else None,
        importance_score=a.importance_score if a else None,
        affected_industries=a.affected_industries if a else [],
        affected_assets=a.affected_assets if a else [],
        causal_chain=a.causal_chain if a else [],
        positive_factors=a.positive_factors if a else [],
        negative_factors=a.negative_factors if a else [],
        risk_warning=a.risk_warning if a else None,
    )


@router.post("/jobs/extract", response_model=ExtractResponse)
def trigger_extract(db: Session = Depends(get_db)) -> ExtractResponse:
    """手动触发一次事件抽取处理。

    从未关联事件的 raw_news 中逐条调用 LLM 抽取结构化事件，按标题相似度
    合并去重后写入 events / event_sources。返回本轮处理统计。
    """
    result = process_all(db)
    # ===== 抽取报告 =====
    print("\n" + "=" * 55)
    print("⚙️  EventAlpha 事件抽取报告")
    print("=" * 55)
    print(f"  处理: {result.processed}, 新建事件: {result.new_events}, "
          f"合并: {result.merged}")
    print(f"  噪声跳过: {result.skipped_noise}, 失败: {result.failed}")
    print("=" * 55 + "\n")
    # =============================
    return result


@router.post("/jobs/analyze", response_model=AnalyzeResponse)
def trigger_analyze(db: Session = Depends(get_db)) -> AnalyzeResponse:
    """手动触发一次事件分析处理。

    从尚未生成分析的 events 中逐条调用 LLM 生成投资影响分析，
    写入 event_analysis。返回本轮处理统计。
    """
    result = analyze_all(db)
    # ===== 分析报告 =====
    print("\n" + "=" * 55)
    print("🧠 EventAlpha 事件分析报告")
    print("=" * 55)
    print(f"  分析成功: {result.analyzed}, 跳过: {result.skipped_existing}, "
          f"失败: {result.failed}")
    print("=" * 55 + "\n")
    # =============================
    return result
