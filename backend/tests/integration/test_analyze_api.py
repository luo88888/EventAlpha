"""POST /api/jobs/analyze 集成测试。

用 conftest 的 db + client fixtures（内存 SQLite），mock LLM 调用。
覆盖：首次分析、重复触发跳过、无事件可分析、LLM 失败隔离。
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.analysis import event_analyzer
from app.core.database import utcnow
from app.models.event import Event
from app.models.event_analysis import EventAnalysis
from app.models.event_source import EventSource
from app.models.raw_news import RawNews
from app.schemas.event import AnalyzedEvent


# ---------- fixtures ----------


@pytest.fixture(autouse=True)
def _reset_model_cache():
    """每个测试前后重置模块级模型缓存，避免测试间干扰。"""
    event_analyzer.reset_model_cache()
    yield
    event_analyzer.reset_model_cache()


def _make_fake_analysis():
    """构造一个固定的 AnalyzedEvent 返回值。"""
    return AnalyzedEvent(
        importance_score=4,
        importance_level="A",
        affected_industries=["新能源", "汽车"],
        affected_assets=["宁德时代", "比亚迪"],
        causal_chain=["政策发布", "行业利好", "相关公司受益"],
        positive_factors=["补贴力度加大"],
        negative_factors=["政策持续性不确定"],
        risk_warning="该分析仅用于事件研究，不构成投资建议。",
    )


@pytest.fixture()
def events_without_analysis(db):
    """构造 2 个无分析的事件（含来源关联）。"""
    rn1 = RawNews(
        source="36kr",
        title="新闻1",
        url="http://example.com/1",
        content_hash="a" * 64,
        summary="摘要1",
        published_at=utcnow(),
    )
    rn2 = RawNews(
        source="wallstreetcn",
        title="新闻2",
        url="http://example.com/2",
        content_hash="b" * 64,
        summary="摘要2",
        published_at=utcnow(),
    )
    db.add_all([rn1, rn2])
    db.flush()

    e1 = Event(
        event_id="EVT_20260625_001",
        event_title="美国宣布对华加征关税",
        event_type="trade",
        event_subject="美国",
        summary="美国宣布对华加征25%关税",
        source_count=1,
        status="new",
        created_at=utcnow() - timedelta(hours=1),
    )
    e2 = Event(
        event_id="EVT_20260625_002",
        event_title="美联储宣布加息",
        event_type="rate",
        event_subject="美联储",
        summary="美联储加息25个基点",
        source_count=1,
        status="new",
    )
    db.add_all([e1, e2])
    db.flush()

    db.add(EventSource(event_id=e1.id, raw_news_id=rn1.id, source_name="36kr"))
    db.add(EventSource(event_id=e2.id, raw_news_id=rn2.id, source_name="wallstreetcn"))
    db.commit()
    return {"e1": e1.id, "e2": e2.id}


@pytest.fixture()
def event_with_analysis(db):
    """构造 1 个已有分析的事件。"""
    e = Event(
        event_id="EVT_20260625_010",
        event_title="已有分析事件",
        event_type="policy",
        summary="此事件已有分析",
        source_count=1,
        status="new",
    )
    db.add(e)
    db.flush()
    db.add(
        EventAnalysis(
            event_id=e.id,
            importance_score=3,
            importance_level="B",
            affected_industries=["金融"],
            affected_assets=[],
            causal_chain=["事件", "影响"],
            positive_factors=[],
            negative_factors=[],
            risk_warning="该分析仅用于事件研究，不构成投资建议。",
            model_version="test-v1",
        )
    )
    db.commit()
    return e.id


# ---------- 测试 ----------


def test_analyze_first_run(client, events_without_analysis, monkeypatch):
    """首次分析：2 个事件全部分析成功。"""
    fake = _make_fake_analysis()
    monkeypatch.setattr(event_analyzer, "_structured_model", type("M", (), {"invoke": lambda s, m: fake})())

    resp = client.post("/api/jobs/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analyzed"] == 2
    assert body["failed"] == 0
    assert body["skipped_existing"] == 0


def test_analyze_then_detail_has_analysis(client, events_without_analysis, monkeypatch):
    """分析后 GET /api/events/{id} 的 analysis 不再是 None。"""
    fake = _make_fake_analysis()
    monkeypatch.setattr(event_analyzer, "_structured_model", type("M", (), {"invoke": lambda s, m: fake})())

    client.post("/api/jobs/analyze")

    eid = events_without_analysis["e1"]
    resp = client.get(f"/api/events/{eid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis"] is not None
    assert body["analysis"]["importance_level"] == "A"
    assert body["analysis"]["importance_score"] == 4
    assert "新能源" in body["analysis"]["affected_industries"]


def test_analyze_then_card_has_fields(client, events_without_analysis, monkeypatch):
    """分析后 GET /api/events/{id}/card 的分析字段有值。"""
    fake = _make_fake_analysis()
    monkeypatch.setattr(event_analyzer, "_structured_model", type("M", (), {"invoke": lambda s, m: fake})())

    client.post("/api/jobs/analyze")

    eid = events_without_analysis["e1"]
    resp = client.get(f"/api/events/{eid}/card")
    assert resp.status_code == 200
    card = resp.json()
    assert card["importance_level"] == "A"
    assert card["importance_score"] == 4
    assert len(card["causal_chain"]) == 3
    assert card["risk_warning"] is not None


def test_analyze_skip_existing(client, events_without_analysis, event_with_analysis, monkeypatch):
    """已有分析的事件被跳过，skipped_existing 不变（未分析事件被分析）。"""
    fake = _make_fake_analysis()
    monkeypatch.setattr(event_analyzer, "_structured_model", type("M", (), {"invoke": lambda s, m: fake})())

    resp = client.post("/api/jobs/analyze")
    body = resp.json()
    # 2 个未分析事件被分析，1 个已有分析的不在待分析列表中
    assert body["analyzed"] == 2
    assert body["skipped_existing"] == 0  # 已分析事件根本不会进入处理列表


def test_analyze_no_events(client, db):
    """无事件可分析时返回 analyzed=0。"""
    resp = client.post("/api/jobs/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analyzed"] == 0
    assert body["failed"] == 0


def test_analyze_llm_failure_isolation(client, events_without_analysis, monkeypatch):
    """LLM 调用失败不中断批次：2 个事件都失败，返回 failed=2。"""

    class FailModel:
        def invoke(self, messages):
            raise RuntimeError("LLM 限流")

    monkeypatch.setattr(event_analyzer, "_structured_model", FailModel())

    resp = client.post("/api/jobs/analyze")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analyzed"] == 0
    assert body["failed"] == 2


def test_analyze_idempotent(client, events_without_analysis, monkeypatch):
    """连续调两次：第二次无事件可分析（第一次全部完成）。"""
    fake = _make_fake_analysis()
    monkeypatch.setattr(event_analyzer, "_structured_model", type("M", (), {"invoke": lambda s, m: fake})())

    resp1 = client.post("/api/jobs/analyze")
    assert resp1.json()["analyzed"] == 2

    resp2 = client.post("/api/jobs/analyze")
    assert resp2.json()["analyzed"] == 0
    assert resp2.json()["failed"] == 0
