"""raw_news 的 Pydantic 响应模型。"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class RawNewsOut(BaseModel):
    """单条原始新闻响应。"""

    id: int
    source: str
    title: str
    summary: str | None
    url: str
    content_hash: str
    published_at: datetime | None
    collected_at: datetime

    model_config = {"from_attributes": True}


class CollectResult(BaseModel):
    """采集任务结果。"""

    source: str
    fetched: int
    new: int
    skipped: int


class CollectResponse(BaseModel):
    """POST /api/jobs/collect 响应。"""

    results: list[CollectResult]
    total_fetched: int
    total_new: int
    total_skipped: int
