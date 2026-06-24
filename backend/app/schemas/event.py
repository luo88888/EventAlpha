"""事件处理层 Pydantic 模型。

- ExtractedEvent：LLM 结构化输出的目标 schema，传给 create_structured_model。
- EventOut：GET /api/events 单条事件响应。
- ExtractResult / ExtractResponse：POST /api/jobs/extract 抽取统计。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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
