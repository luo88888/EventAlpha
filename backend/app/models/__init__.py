"""ORM 模型集合。

import 所有模型把表注册到 Base.metadata，供 Alembic autogenerate 发现全部表。
新增模型在此追加 import 与 __all__。
"""

from __future__ import annotations

from app.core.database import Base
from app.models.event import Event
from app.models.event_analysis import EventAnalysis
from app.models.event_source import EventSource
from app.models.raw_news import RawNews

__all__ = ["Base", "RawNews", "Event", "EventSource", "EventAnalysis"]
