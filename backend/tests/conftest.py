"""测试公共 fixtures。

集成测试用内存 SQLite + 依赖注入 override get_db，与生产库 backend/eventalpha.db
隔离。从 backend/ 目录运行（pyproject 已配 pythonpath=["."]）。

import app.main 会触发模块级 setup_logging()（向 logs/ 写日志），可接受。
"""

from __future__ import annotations

from collections.abc import Generator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db, utcnow
from app.main import app
from app.models import Event, EventAnalysis, EventSource, RawNews, User  # noqa: F401 注册全部表


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """内存 SQLite 会话。

    StaticPool 保证全程单连接，使连接级 PRAGMA foreign_keys=ON 生效
    （ondelete=CASCADE 在测试中也需要外键约束）。
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @sa_event.listens_for(engine, "connect")
    def _enable_fk(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """TestClient + override get_db 指向测试会话。"""

    def _override_get_db() -> Generator[Session, None, None]:
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def sample_data(db: Session) -> dict:
    """构造样本：1 个有分析事件 + 1 个无分析事件，含来源关联。

    返回 {"with_analysis": id, "no_analysis": id}，供测试按 id 请求。
    """
    # 原始新闻：已写 event_sources 关联，extract_status 显式设 extracted，
    # 避免被处理层当 pending 重取
    rn = RawNews(
        source="36kr",
        title="测试新闻原文标题",
        url="http://example.com/1",
        content_hash="h" * 64,
        summary="原文摘要",
        published_at=utcnow(),
        extract_status="extracted",
    )
    db.add(rn)
    db.flush()

    # 有分析事件（显式更早创建，验证 created_at 倒序时排在无分析事件之后）
    e1 = Event(
        event_id="EVT_20260625_001",
        event_title="有分析测试事件",
        event_type="policy",
        event_subject="测试主体",
        event_time=utcnow(),
        summary="事件摘要A",
        source_count=1,
        status="new",
        created_at=utcnow() - timedelta(hours=1),
    )
    db.add(e1)
    db.flush()
    db.add(EventSource(event_id=e1.id, raw_news_id=rn.id, source_name="36kr"))
    db.add(
        EventAnalysis(
            event_id=e1.id,
            importance_score=4,
            importance_level="A",
            affected_industries=["新能源", "汽车零部件"],
            affected_assets=["相关行业 ETF"],
            causal_chain=["关税上升", "出口成本提高", "企业利润率承压"],
            positive_factors=["国内替代供应链可能受益"],
            negative_factors=["出口企业成本不确定性上升"],
            risk_warning="该分析仅用于事件研究，不构成投资建议。",
            model_version="test-v1",
        )
    )

    # 无分析事件（较晚创建，倒序时排第一）
    e2 = Event(
        event_id="EVT_20260625_002",
        event_title="无分析测试事件",
        event_type="tech",
        summary="事件摘要B",
        source_count=1,
        status="new",
    )
    db.add(e2)
    db.commit()
    return {"with_analysis": e1.id, "no_analysis": e2.id}
