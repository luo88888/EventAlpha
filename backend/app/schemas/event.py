"""事件处理层 + 推理分析层 Pydantic 模型。

- ExtractedEvent：LLM 结构化输出的目标 schema，传给 create_structured_model。
- AnalyzedEvent：LLM 分析输出 schema，传给 create_structured_model。
- EventOut：GET /api/events 单条事件响应。
- ExtractResult / ExtractResponse：POST /api/jobs/extract 抽取统计。
- AnalyzeResult / AnalyzeResponse：POST /api/jobs/analyze 分析统计。
- EventSourceOut / AnalysisOut / EventDetail / EventCard：Day 5 产品服务层
  事件详情、事件卡片接口响应（见 docs/EventAlpha_MVP一周项目计划.md 第 6 节）。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ExtractedEvent(BaseModel):
    """LLM 事件抽取的结构化输出 schema。

    event_type 取值集合由 Prompt 约束：
    policy / trade / rate / tech / company / disaster / geopolitical / other。
    """

    event_title: str = Field(description="事件标题：一句客观完整的话概括事件")
    # event_type 取值集合由 Prompt 约束（见 config/prompts/event_extraction.txt）
    event_type: str = Field(
        description="事件类型：policy/trade/rate/tech/company/disaster/geopolitical/other"
    )
    event_subject: str | None = Field(default=None, description="事件主体：国家/公司/机构/行业名称")
    event_time: datetime | None = Field(
        default=None, description="事件时间 ISO 8601；无法判断时留空"
    )
    summary: str = Field(description="事件摘要：2-3 句客观陈述")

    @field_validator("event_time", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        """LLM 有时返回空字符串而非 null，统一转为 None。"""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v


class EventOut(BaseModel):
    """GET /api/events 单条事件响应。"""

    id: int
    event_id: str
    event_title: str
    event_type: str
    event_subject: str | None
    event_time: datetime | None
    summary: str | None
    source_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExtractResult(BaseModel):
    """单次抽取任务统计。"""

    processed: int = Field(description="本轮处理的原始新闻数")
    new_events: int = Field(description="本轮新建事件数")
    merged: int = Field(description="本轮合并到既有事件的次数")
    skipped_noise: int = Field(description="被 LLM 判定为非事件(other)而跳过的条数")
    failed: int = Field(description="抽取/入库失败被隔离的条数")


class ExtractResponse(ExtractResult):
    """POST /api/jobs/extract 响应（含统计 + 汇总）。"""


class EventSourceOut(BaseModel):
    """事件来源项：来源名（EventSource 快照）+ 原始新闻摘要信息（RawNews）。

    字段跨两张表：source_name 来自 event_sources，其余来自 raw_news。
    由详情端点手动映射（from_attributes 无法自动读 es.raw_news.title）。
    """

    source_name: str | None
    title: str
    url: str
    source: str
    published_at: datetime | None

    model_config = {"from_attributes": True}


class AnalysisOut(BaseModel):
    """事件分析块（可空）。字段对齐 EventAnalysis，一对一。"""

    importance_score: int
    importance_level: str
    affected_industries: list
    affected_assets: list
    causal_chain: list
    positive_factors: list
    negative_factors: list
    risk_warning: str | None
    model_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventDetail(BaseModel):
    """GET /api/events/{id} 响应：事件主信息 + 来源列表 + 分析块。

    analysis 为 None 表示事件尚未生成分析（Day 4 推理分析层产物）。
    """

    id: int
    event_id: str
    event_title: str
    event_type: str
    event_subject: str | None
    event_time: datetime | None
    summary: str | None
    source_count: int
    status: str
    created_at: datetime
    sources: list[EventSourceOut] = []
    analysis: AnalysisOut | None = None

    model_config = {"from_attributes": True}


class EventCard(BaseModel):
    """GET /api/events/{id}/card 响应：事件卡片（计划第 6 节字段）。

    跨表扁平视图：基础字段来自 events，分析字段来自 event_analysis。
    卡片用 ``title``（非 event_title），由端点从 events.event_title 映射。
    事件尚未分析时，分析字段降级为 None / 空数组，前端可安全渲染。
    """

    event_id: str
    title: str
    event_type: str
    summary: str | None
    source_count: int
    importance_level: str | None = None
    importance_score: int | None = None
    affected_industries: list = []
    affected_assets: list = []
    causal_chain: list = []
    positive_factors: list = []
    negative_factors: list = []
    risk_warning: str | None = None


class AnalyzedEvent(BaseModel):
    """LLM 分析输出 schema，传给 create_structured_model(AnalyzedEvent)。

    importance_score 1-5，importance_level S/A/B/C，Prompt 约束两者自洽。
    """

    importance_score: int = Field(ge=1, le=5, description="重要性评分 1-5")
    importance_level: str = Field(description="重要性等级 S/A/B/C")
    affected_industries: list[str] = Field(description="受影响行业列表")
    affected_assets: list[str] = Field(description="受影响资产/公司列表")
    causal_chain: list[str] = Field(description="因果传导链：事件→传导→市场影响")
    positive_factors: list[str] = Field(description="正面影响因素")
    negative_factors: list[str] = Field(description="负面影响因素")
    risk_warning: str = Field(description="风险提示")


class AnalyzeResult(BaseModel):
    """单次分析任务统计。"""

    analyzed: int = Field(description="本轮分析成功的事件数")
    skipped_existing: int = Field(description="已有分析而跳过的事件数")
    failed: int = Field(description="分析失败的事件数")


class AnalyzeResponse(AnalyzeResult):
    """POST /api/jobs/analyze 响应。"""
