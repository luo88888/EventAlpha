"""采集接口：POST /api/jobs/collect — 手动触发 RSS 采集。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.collectors.rss_collector import collect_all
from app.core.database import get_db
from app.schemas.raw_news import CollectResponse, CollectResult

router = APIRouter()


@router.post("/jobs/collect", response_model=CollectResponse)
def trigger_collect(db: Session = Depends(get_db)) -> CollectResponse:
    """手动触发一次 RSS 采集。

    拉取所有配置的 RSS 源，按 content_hash 去重后写入 raw_news。
    返回每个源的采集统计。
    """
    stats = collect_all(db)
    # ===== 采集报告 =====
    print("\n" + "=" * 55)
    print("📡  EventAlpha 数据采集报告")
    print("=" * 55)
    for s in stats:
        print(f"  [{s.source}] 获取: {s.fetched}, 入库: {s.new}, 跳过: {s.skipped}")
    print("-" * 55)
    print(f"  总计: 获取 {sum(s.fetched for s in stats)}, "
          f"入库 {sum(s.new for s in stats)}, "
          f"跳过 {sum(s.skipped for s in stats)}")
    print("=" * 55 + "\n")
    # =============================
    results = [
        CollectResult(
            source=s.source,
            fetched=s.fetched,
            new=s.new,
            skipped=s.skipped,
        )
        for s in stats
    ]
    return CollectResponse(
        results=results,
        total_fetched=sum(s.fetched for s in stats),
        total_new=sum(s.new for s in stats),
        total_skipped=sum(s.skipped for s in stats),
    )
