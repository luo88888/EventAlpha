"""推理分析层单测。

覆盖：
- AnalyzedEvent schema 约束（score 范围、level 枚举）
- Prompt 模板可加载、占位符完整
- analyze_event 在 LLM 异常时返回 None（mock）
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.event import AnalyzedEvent


# ---------- AnalyzedEvent schema 约束 ----------


def test_analyzed_event_valid() -> None:
    """合法数据可构造。"""
    a = AnalyzedEvent(
        importance_score=4,
        importance_level="A",
        affected_industries=["新能源"],
        affected_assets=["宁德时代"],
        causal_chain=["政策发布", "行业利好", "股价上涨"],
        positive_factors=["补贴增加"],
        negative_factors=["政策不确定性"],
        risk_warning="该分析仅用于事件研究，不构成投资建议。",
    )
    assert a.importance_score == 4
    assert a.importance_level == "A"


def test_analyzed_event_score_too_high() -> None:
    """score > 5 应报错。"""
    with pytest.raises(ValidationError):
        AnalyzedEvent(
            importance_score=6,
            importance_level="S",
            affected_industries=[],
            affected_assets=[],
            causal_chain=[],
            positive_factors=[],
            negative_factors=[],
            risk_warning="test",
        )


def test_analyzed_event_score_zero() -> None:
    """score = 0 应报错。"""
    with pytest.raises(ValidationError):
        AnalyzedEvent(
            importance_score=0,
            importance_level="C",
            affected_industries=[],
            affected_assets=[],
            causal_chain=[],
            positive_factors=[],
            negative_factors=[],
            risk_warning="test",
        )


def test_analyzed_event_empty_lists_ok() -> None:
    """空列表是合法值（某些事件确实无明确影响行业）。"""
    a = AnalyzedEvent(
        importance_score=1,
        importance_level="C",
        affected_industries=[],
        affected_assets=[],
        causal_chain=["事件发生", "无显著市场影响"],
        positive_factors=[],
        negative_factors=[],
        risk_warning="该分析仅用于事件研究，不构成投资建议。",
    )
    assert a.affected_industries == []


# ---------- Prompt 模板 ----------


def test_prompt_template_loadable() -> None:
    """Prompt 模板文件存在且包含必填占位符。"""
    path = Path("config/prompts/event_analysis.txt")
    assert path.exists(), f"Prompt 模板缺失：{path}"
    content = path.read_text(encoding="utf-8")
    for placeholder in ["{event_title}", "{event_type}", "{event_subject}", "{summary}"]:
        assert placeholder in content, f"模板缺少占位符 {placeholder}"


# ---------- analyze_event 异常隔离 ----------


def test_analyze_event_returns_none_on_exception(monkeypatch) -> None:
    """LLM 调用抛异常时返回 None，不向上传播。"""
    from app.analysis import event_analyzer

    # mock _get_structured_model 返回一个会抛异常的 mock
    class FakeModel:
        def invoke(self, messages):
            raise RuntimeError("LLM 限流")

    monkeypatch.setattr(event_analyzer, "_structured_model", FakeModel())

    # 构造一个最小 Event 对象（不走 DB）
    from app.models.event import Event

    fake_event = Event(
        id=1,
        event_id="EVT_20260625_001",
        event_title="测试事件",
        event_type="policy",
        summary="测试摘要",
    )
    result = event_analyzer.analyze_event(fake_event)
    assert result is None
