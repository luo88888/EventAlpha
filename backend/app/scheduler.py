"""定时任务：每 INTERVAL_MINUTES 分钟自动执行 采集→抽取→分析 流水线。

在 FastAPI lifespan 中启动后台线程，shutdown 时通过 Event 优雅退出。
流水线串行执行：collect → extract → analyze，单步失败不阻塞后续步骤。
"""

from __future__ import annotations

import logging
import threading
from datetime import UTC, datetime

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 采集间隔（秒）
INTERVAL_SECONDS = 30 * 60  # 30 分钟

# 启动后首次执行的延迟（秒），避免启动时和其他初始化冲突
_INITIAL_DELAY = 10


def _run_pipeline(db: Session) -> None:
    """执行完整流水线：采集 → 抽取 → 分析。"""
    from app.analysis.analysis_processor import analyze_all
    from app.collectors.rss_collector import collect_all
    from app.processors.event_processor import process_all

    now = datetime.now(UTC).strftime("%H:%M:%S")
    logger.info("定时流水线开始 %s", now)

    # 1. 采集
    try:
        stats = collect_all(db)
        total_new = sum(s.new for s in stats)
        logger.info("采集完成: 入库 %d 条", total_new)
    except Exception as e:  # noqa: BLE001
        logger.error("采集失败: %s", e)

    # 2. 抽取
    try:
        result = process_all(db)
        logger.info("抽取完成: 新事件 %d", result.new_events)
    except Exception as e:  # noqa: BLE001
        logger.error("抽取失败: %s", e)

    # 3. 分析
    try:
        result = analyze_all(db)
        logger.info("分析完成: %d 成功, %d 失败", result.analyzed, result.failed)
    except Exception as e:  # noqa: BLE001
        logger.error("分析失败: %s", e)

    logger.info("定时流水线结束")


def _scheduler_loop(stop_event: threading.Event) -> None:
    """后台线程主循环：首次延迟后执行，之后每 INTERVAL_SECONDS 执行一次。"""
    from app.core.database import SessionLocal

    # 首次延迟
    logger.info("定时任务将在 %ds 后首次执行", _INITIAL_DELAY)
    if stop_event.wait(_INITIAL_DELAY):
        return

    while not stop_event.is_set():
        db = SessionLocal()
        try:
            _run_pipeline(db)
        finally:
            db.close()

        # 等待下一轮，可被 stop_event 中断
        if stop_event.wait(INTERVAL_SECONDS):
            break


def start_scheduler() -> threading.Event:
    """启动定时任务后台线程，返回 stop_event 用于优雅关闭。"""
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_scheduler_loop,
        args=(stop_event,),
        name="pipeline-scheduler",
        daemon=True,
    )
    thread.start()
    logger.info("定时任务已启动（每 %d 分钟）", INTERVAL_SECONDS // 60)
    return stop_event


def stop_scheduler(stop_event: threading.Event) -> None:
    """停止定时任务。"""
    stop_event.set()
    logger.info("定时任务已停止")
