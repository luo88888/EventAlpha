"""事件接口：

- GET /api/events：事件列表（支持 event_type 过滤，按 created_at 倒序）。
- POST /api/jobs/extract：手动触发一次事件抽取处理。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.event import Event
from app.processors.event_processor import process_all
from app.schemas.event import EventOut, ExtractResponse

router = APIRouter()


@router.get("/events", response_model=list[EventOut])
def list_events(
    event_type: str | None = Query(default=None, description="按事件类型过滤"),
    limit: int = Query(default=50, ge=1, le=200, description="返回条数上限"),
    db: Session = Depends(get_db),
) -> list[Event]:
    """事件列表。

    按 created_at 倒序返回，支持按 event_type 过滤。MVP 阶段不含分页游标，
    用 limit 限定条数（Day 5 产品服务层再细化筛选与分页）。
    """
    stmt = select(Event).order_by(Event.created_at.desc()).limit(limit)
    if event_type:
        stmt = stmt.where(Event.event_type == event_type)
    return list(db.scalars(stmt).all())


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
