"""事件处理层 process_all 状态流转单测。

覆盖 processors/event_processor.py 的 extract_status 不变量：
- 新建新闻默认 pending
- _load_unprocessed_news 只取 pending
- process_all 三种结局正确设状态（failed / noise / extracted）
- 标记后不再被 _load_unprocessed_news 重取（核心不变量）

mock extract_event 按 news.title 模拟三种结局，不真调 LLM。
"""

from __future__ import annotations

import hashlib
from datetime import timedelta

from app.core.database import utcnow
from app.models.event import Event
from app.models.event_source import EventSource
from app.models.raw_news import (
    EXTRACT_STATUS_EXTRACTED,
    EXTRACT_STATUS_FAILED,
    EXTRACT_STATUS_NOISE,
    EXTRACT_STATUS_PENDING,
    RawNews,
)
from app.processors import event_processor
from app.processors.event_processor import _load_unprocessed_news, process_all
from app.schemas.event import ExtractedEvent


def _make_news(
    title: str, *, status: str = EXTRACT_STATUS_PENDING, url: str | None = None
) -> RawNews:
    """构造一条 RawNews，content_hash 由 title 唯一生成避免 UNIQUE 冲突。"""
    return RawNews(
        source="test",
        title=title,
        url=url or f"http://example.com/{title}",
        content_hash=hashlib.sha256(title.encode()).hexdigest(),
        summary="摘要",
        published_at=utcnow(),
        collected_at=utcnow(),
        extract_status=status,
    )


def _fake_extract_factory():
    """构造一个按 news.title 决定结局的 fake extract_event。

    约定：
    - title 含 "FAIL" → 返回 None（失败）
    - title 含 "NOISE" → 返回 event_type="other"（噪声）
    - 其他 → 返回正常 ExtractedEvent（event_type 由 title 前缀推断，默认 trade）
    """
    def _fake(news: RawNews) -> ExtractedEvent | None:
        if "FAIL" in news.title:
            return None
        if "NOISE" in news.title:
            return ExtractedEvent(
                event_title=news.title,
                event_type="other",
                event_subject=None,
                event_time=None,
                summary="噪声摘要",
            )
        etype = "trade"
        if news.title.startswith("政策"):
            etype = "policy"
        return ExtractedEvent(
            event_title=news.title,
            event_type=etype,
            event_subject="测试主体",
            event_time=utcnow(),
            summary="事件摘要",
        )
    return _fake


# ── 1. 默认值 ──────────────────────────────────────────────
def test_new_news_default_pending(db) -> None:
    """新建 RawNews 不传 extract_status，默认 pending。"""
    rn = _make_news("默认状态新闻")
    db.add(rn)
    db.commit()
    assert rn.extract_status == EXTRACT_STATUS_PENDING


# ── 2. 查询只取 pending ────────────────────────────────────
def test_load_unprocessed_only_pending(db) -> None:
    """四种状态各一条，_load_unprocessed_news 只返回 pending。"""
    news_map = {
        EXTRACT_STATUS_PENDING: _make_news("待处理新闻"),
        EXTRACT_STATUS_EXTRACTED: _make_news("已处理新闻", status=EXTRACT_STATUS_EXTRACTED),
        EXTRACT_STATUS_NOISE: _make_news("噪声新闻", status=EXTRACT_STATUS_NOISE),
        EXTRACT_STATUS_FAILED: _make_news("失败新闻", status=EXTRACT_STATUS_FAILED),
    }
    db.add_all(list(news_map.values()))
    db.commit()

    loaded = _load_unprocessed_news(db)
    loaded_titles = [n.title for n in loaded]
    assert loaded_titles == ["待处理新闻"]


# ── 3. 噪声标记 ────────────────────────────────────────────
def test_process_all_marks_noise(db, monkeypatch) -> None:
    """LLM 判 other → 状态变 noise、未建事件。"""
    db.add(_make_news("某NOISE新闻"))
    db.commit()
    monkeypatch.setattr(event_processor, "extract_event", _fake_extract_factory())

    result = process_all(db)

    rn = db.query(RawNews).filter_by(title="某NOISE新闻").one()
    assert rn.extract_status == EXTRACT_STATUS_NOISE
    assert result.skipped_noise == 1
    assert result.failed == 0
    assert result.new_events == 0
    assert db.query(Event).count() == 0


# ── 4. 失败标记 ────────────────────────────────────────────
def test_process_all_marks_failed(db, monkeypatch) -> None:
    """extract_event 返回 None → 状态变 failed、未建事件。"""
    db.add(_make_news("某FAIL新闻"))
    db.commit()
    monkeypatch.setattr(event_processor, "extract_event", _fake_extract_factory())

    result = process_all(db)

    rn = db.query(RawNews).filter_by(title="某FAIL新闻").one()
    assert rn.extract_status == EXTRACT_STATUS_FAILED
    assert result.failed == 1
    assert result.skipped_noise == 0
    assert result.new_events == 0
    assert db.query(Event).count() == 0


# ── 5. 新建事件标 extracted ─────────────────────────────────
def test_process_all_marks_extracted_on_new_event(db, monkeypatch) -> None:
    """正常抽取 → 新建事件、写 event_sources、news 状态变 extracted。"""
    db.add(_make_news("关税政策出台"))
    db.commit()
    monkeypatch.setattr(event_processor, "extract_event", _fake_extract_factory())

    result = process_all(db)

    rn = db.query(RawNews).filter_by(title="关税政策出台").one()
    assert rn.extract_status == EXTRACT_STATUS_EXTRACTED
    assert result.new_events == 1
    assert result.failed == 0
    assert result.skipped_noise == 0
    assert db.query(Event).count() == 1
    assert db.query(EventSource).count() == 1


# ── 6. 合并路径标 extracted ─────────────────────────────────
def test_process_all_marks_extracted_on_merge(db, monkeypatch) -> None:
    """已有相似事件 → 走合并路径，news 状态仍变 extracted。"""
    # 先建一个既有事件（并提供合并候选）
    e = Event(
        event_id="EVT_20260712_001",
        event_title="美国宣布对华加征关税",
        event_type="trade",
        event_subject="美国",
        event_time=utcnow(),
        summary="既有事件摘要",
        source_count=1,
        status="new",
        created_at=utcnow() - timedelta(hours=1),
    )
    db.add(e)
    db.flush()
    # 待处理新闻：标题与既有事件高度重叠（bigram 覆盖度 ≥ 0.6），同类型 trade
    db.add(_make_news("美国对华加征关税政策正式宣布"))
    db.commit()
    monkeypatch.setattr(event_processor, "extract_event", _fake_extract_factory())

    result = process_all(db)

    rn = db.query(RawNews).filter_by(title="美国对华加征关税政策正式宣布").one()
    assert rn.extract_status == EXTRACT_STATUS_EXTRACTED
    assert result.merged == 1
    assert result.new_events == 0
    # 事件总数不变（合并而非新建），但 event_sources 多一条
    assert db.query(Event).count() == 1
    assert db.query(EventSource).count() == 1


# ── 7. 噪声标记后不再重取（核心不变量）─────────────────────
def test_marked_noise_not_reloaded(db, monkeypatch) -> None:
    """跑两轮：噪声标 noise 后，第二轮不再被 _load_unprocessed_news 取出。"""
    db.add(_make_news("某NOISE新闻"))
    db.add(_make_news("关税政策出台"))
    db.commit()

    call_count = {"n": 0}
    fake = _fake_extract_factory()

    def _counting_fake(news):
        call_count["n"] += 1
        return fake(news)

    monkeypatch.setattr(event_processor, "extract_event", _counting_fake)

    process_all(db)  # 第一轮：处理 2 条（1 噪声 + 1 正常）
    first_calls = call_count["n"]
    assert first_calls == 2

    process_all(db)  # 第二轮：无 pending，不应再调 LLM
    assert call_count["n"] == first_calls  # 调用次数不增加


# ── 8. 失败标记后不再重试（核心不变量）─────────────────────
def test_marked_failed_not_reloaded(db, monkeypatch) -> None:
    """跑两轮：失败标 failed 后，第二轮不再重试。"""
    db.add(_make_news("某FAIL新闻"))
    db.add(_make_news("关税政策出台"))
    db.commit()

    call_count = {"n": 0}
    fake = _fake_extract_factory()

    def _counting_fake(news):
        call_count["n"] += 1
        return fake(news)

    monkeypatch.setattr(event_processor, "extract_event", _counting_fake)

    process_all(db)  # 第一轮：处理 2 条
    first_calls = call_count["n"]
    assert first_calls == 2

    process_all(db)  # 第二轮：无 pending
    assert call_count["n"] == first_calls  # 失败新闻不再重试


# ── 额外：混合批次统计正确 ──────────────────────────────────
def test_process_all_mixed_batch_stats(db, monkeypatch) -> None:
    """一个批次里 failed/noise/extracted 混合，统计与状态均正确。"""
    db.add(_make_news("某FAIL新闻"))
    db.add(_make_news("某NOISE新闻"))
    db.add(_make_news("政策关税出台A"))
    db.add(_make_news("政策关税出台B"))  # 与 A 高度重叠，应合并到 A
    db.commit()
    monkeypatch.setattr(event_processor, "extract_event", _fake_extract_factory())

    result = process_all(db)

    assert result.failed == 1
    assert result.skipped_noise == 1
    assert result.new_events == 1  # A 新建
    assert result.merged == 1      # B 合并到 A
    assert result.processed == 2   # A + B（fail/noise 不计入 processed）

    statuses = {n.title: n.extract_status for n in db.query(RawNews).all()}
    assert statuses["某FAIL新闻"] == EXTRACT_STATUS_FAILED
    assert statuses["某NOISE新闻"] == EXTRACT_STATUS_NOISE
    assert statuses["政策关税出台A"] == EXTRACT_STATUS_EXTRACTED
    assert statuses["政策关税出台B"] == EXTRACT_STATUS_EXTRACTED
