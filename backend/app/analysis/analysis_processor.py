"""分析编排：读未分析事件 → 并发 LLM 分析 → 写 event_analysis。

模式对齐 processors/event_processor.py：
- 未分析判定：events.id NOT IN (SELECT event_id FROM event_analysis)，零 schema 变更。
- 并发分析：ThreadPoolExecutor 并行调用 LLM，max_workers 控制并发度。
- 单条失败不中断整批，限流自动重试（event_analyzer 内置指数退避）。
- model_version 记录 LLM provider + model。
- db.commit() 失败则 rollback，统计归零。
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.event_analyzer import analyze_event
from app.models.event import Event
from app.models.event_analysis import EventAnalysis
from app.schemas.event import AnalyzeResult
from utils.config_handler import load_llm_config

logger = logging.getLogger(__name__)

# 并发度：小米等无限流 API 可调高；DeepSeek 限流时建议 1-3
_MAX_WORKERS = 200


def _load_unanalyzed_events(db: Session) -> list[Event]:
    """查询尚未生成分析的事件。

    已分析 = events.id 存在于 event_analysis.event_id。
    """
    stmt = (
        select(Event)
        .where(
            ~Event.id.in_(select(EventAnalysis.event_id).where(EventAnalysis.event_id.is_not(None)))
        )
        .order_by(Event.created_at)
    )
    return list(db.scalars(stmt).all())


def analyze_all(db: Session) -> AnalyzeResult:
    """处理一批未分析事件：并发调用 LLM 分析，写入 event_analysis。

    Args:
        db: 数据库会话（由调用方负责提交/关闭；本函数内部 commit）。

    Returns:
        AnalyzeResult：本轮处理统计。
    """
    events = _load_unanalyzed_events(db)
    if not events:
        logger.info("没有待分析的事件")
        return AnalyzeResult(analyzed=0, skipped_existing=0, failed=0)

    # model_version 记录本次使用的 provider/model
    llm_config = load_llm_config()
    model_version = f"{llm_config.default_provider}/{llm_config.default_model}"

    # 并发分析：每个 event 在线程中独立调用 LLM
    results: dict[int, object] = {}  # event.id -> AnalyzedEvent | None
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        future_to_event = {executor.submit(analyze_event, event): event for event in events}
        for future in as_completed(future_to_event):
            event = future_to_event[future]
            try:
                results[event.id] = future.result()
            except Exception as e:  # noqa: BLE001
                logger.error("分析事件异常 event_id=%s: %s", event.id, e)
                results[event.id] = None

    # 收集结果，写入 DB
    analyzed = 0
    failed = 0

    for event in events:
        result = results.get(event.id)
        if result is None:
            failed += 1
            continue

        analysis = EventAnalysis(
            event_id=event.id,
            importance_score=result.importance_score,
            importance_level=result.importance_level,
            affected_industries=result.affected_industries,
            affected_assets=result.affected_assets,
            causal_chain=result.causal_chain,
            positive_factors=result.positive_factors,
            negative_factors=result.negative_factors,
            risk_warning=result.risk_warning,
            model_version=model_version,
        )
        db.add(analysis)
        analyzed += 1
        logger.info("分析完成 event_id=%s level=%s", event.event_id, result.importance_level)

    try:
        db.commit()
    except Exception as e:  # noqa: BLE001
        logger.error("分析批次提交失败: %s", e)
        db.rollback()
        return AnalyzeResult(analyzed=0, skipped_existing=0, failed=failed + analyzed)

    logger.info("分析处理完成: analyzed=%d, failed=%d", analyzed, failed)
    return AnalyzeResult(analyzed=analyzed, skipped_existing=0, failed=failed)
