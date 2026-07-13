"""统计聚合接口的 Pydantic 响应模型。

GET /api/stats 返回 Dashboard 仪表盘所需的聚合数据：
事件总数/各等级计数、事件类型分布、重要性等级分布、近 14 天趋势、来源分布、
S·A 级重要事件 Top 列表。

纯只读聚合，不落库、不加迁移。字段名与前端 lib/types.ts 的 StatsOut 逐字对齐。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TypeCount(BaseModel):
    """事件类型分布单项。"""

    type: str
    count: int


class LevelCount(BaseModel):
    """重要性等级分布单项。level 为 "none" 表示尚未生成分析的事件。"""

    level: str
    count: int


class TrendPoint(BaseModel):
    """按日期聚合的事件趋势点。date 为 YYYY-MM-DD。"""

    date: str
    count: int


class SourceCount(BaseModel):
    """采集来源分布单项。"""

    source: str
    count: int


class TopEvent(BaseModel):
    """重要事件流单项（S·A 级，按分数降序）。"""

    id: int
    event_id: str
    event_title: str
    event_type: str
    importance_level: str | None
    importance_score: int | None
    created_at: datetime


class StatsOut(BaseModel):
    """GET /api/stats 响应：仪表盘聚合数据。

    totals 四个键：events / analyzed / sources / raw_news。
    level_distribution 含 "none" 项统计尚未分析的事件数。
    trend 为近 14 天（含无事件日补零）按日期升序。
    top_events 最多 8 条，仅 S·A 级，按 importance_score 降序。
    """

    totals: dict[str, int]
    type_distribution: list[TypeCount]
    level_distribution: list[LevelCount]
    trend: list[TrendPoint]
    source_distribution: list[SourceCount]
    top_events: list[TopEvent]
