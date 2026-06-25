"""Day 5 事件接口集成测试。

覆盖 GET /api/events 列表筛选、GET /api/events/{id} 详情、GET /api/events/{id}/card
卡片（含无分析降级）。用 conftest 的 client + sample_data fixtures，内存 SQLite 隔离。
"""

from __future__ import annotations

from datetime import timedelta

from app.core.database import utcnow

# ---------- 列表筛选 ----------


def test_list_events_default(client, sample_data):
    """默认返回列表，按 created_at 倒序（无分析事件较晚创建，排第一）。"""
    resp = client.get("/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["id"] == sample_data["no_analysis"]
    assert data[1]["id"] == sample_data["with_analysis"]


def test_list_events_filter_by_type(client, sample_data):
    """event_type=policy 只回 policy 事件。"""
    resp = client.get("/api/events", params={"event_type": "policy"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_data["with_analysis"]


def test_list_events_filter_importance_inner_join(client, sample_data):
    """importance_level=A 只回有分析且等级为 A 的事件（无分析事件被 INNER JOIN 排除）。"""
    resp = client.get("/api/events", params={"importance_level": "A"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_data["with_analysis"]


def test_list_events_no_importance_returns_all(client, sample_data):
    """不传 importance_level 时不加 JOIN，返回全部（含无分析事件）。"""
    resp = client.get("/api/events")
    data = resp.json()
    assert len(data) == 2
    ids = {e["id"] for e in data}
    assert sample_data["no_analysis"] in ids


def test_list_events_time_range(client, sample_data):
    """start_time/end_time 按 created_at 过滤：未来区间排除全部。"""
    future = (utcnow() + timedelta(days=1)).isoformat()
    resp = client.get("/api/events", params={"start_time": future})
    assert resp.status_code == 200
    assert resp.json() == []

    # 过去区间包含全部
    past = (utcnow() - timedelta(days=1)).isoformat()
    resp = client.get("/api/events", params={"start_time": past})
    assert len(resp.json()) == 2


def test_list_events_offset(client, sample_data):
    """offset 跳过第一条，只剩一条。"""
    resp = client.get("/api/events", params={"offset": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


# ---------- 详情 ----------


def test_detail_200(client, sample_data):
    """详情含主信息、sources 与 analysis。"""
    eid = sample_data["with_analysis"]
    resp = client.get(f"/api/events/{eid}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == eid
    assert body["event_title"] == "有分析测试事件"
    assert len(body["sources"]) == 1
    assert body["analysis"] is not None
    assert body["analysis"]["importance_level"] == "A"


def test_detail_404(client, sample_data):
    """不存在的 id 返回 404。"""
    resp = client.get("/api/events/99999")
    assert resp.status_code == 404


def test_detail_sources_cross_table(client, sample_data):
    """sources[0].title 来自 raw_news.title（跨表映射）。"""
    eid = sample_data["with_analysis"]
    resp = client.get(f"/api/events/{eid}")
    src = resp.json()["sources"][0]
    assert src["title"] == "测试新闻原文标题"
    assert src["url"] == "http://example.com/1"
    assert src["source"] == "36kr"
    assert src["source_name"] == "36kr"


def test_detail_no_analysis(client, sample_data):
    """无分析事件详情的 analysis 为 None，sources 为空列表。"""
    eid = sample_data["no_analysis"]
    resp = client.get(f"/api/events/{eid}")
    body = resp.json()
    assert body["analysis"] is None
    assert body["sources"] == []


# ---------- 卡片 ----------


def test_card_200_full(client, sample_data):
    """有分析卡片全字段：title 来自 event_title，causal_chain 等完整。"""
    eid = sample_data["with_analysis"]
    resp = client.get(f"/api/events/{eid}/card")
    assert resp.status_code == 200
    card = resp.json()
    assert card["event_id"] == "EVT_20260625_001"
    assert card["title"] == "有分析测试事件"
    assert card["event_type"] == "policy"
    assert card["source_count"] == 1
    assert card["importance_level"] == "A"
    assert card["importance_score"] == 4
    assert card["affected_industries"] == ["新能源", "汽车零部件"]
    assert len(card["causal_chain"]) == 3
    assert card["risk_warning"] is not None


def test_card_no_analysis_degraded(client, sample_data):
    """无分析事件卡片降级：分析字段为 None / 空数组，不报错。"""
    eid = sample_data["no_analysis"]
    resp = client.get(f"/api/events/{eid}/card")
    assert resp.status_code == 200
    card = resp.json()
    assert card["title"] == "无分析测试事件"
    assert card["importance_level"] is None
    assert card["importance_score"] is None
    assert card["affected_industries"] == []
    assert card["affected_assets"] == []
    assert card["causal_chain"] == []
    assert card["positive_factors"] == []
    assert card["negative_factors"] == []
    assert card["risk_warning"] is None


def test_card_404(client, sample_data):
    """不存在的 id 卡片返回 404。"""
    resp = client.get("/api/events/99999/card")
    assert resp.status_code == 404


def test_card_field_rename(client, sample_data):
    """卡片用 title（非 event_title），值来自 events.event_title。"""
    eid = sample_data["with_analysis"]
    card = client.get(f"/api/events/{eid}/card").json()
    assert "title" in card
    assert "event_title" not in card
