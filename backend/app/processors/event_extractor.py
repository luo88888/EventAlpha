"""事件抽取器：单条 RawNews → LLM 结构化抽取 → ExtractedEvent。

- Prompt 模板外置于 config/prompts/event_extraction.txt，启动时读取一次并缓存。
- 通过 create_structured_model(ExtractedEvent) 让 LLM 直接产出 schema 实例，无需自解析 JSON。
- event_time 为空时回退 raw_news.published_at。
- 单条抽取失败时记日志返回 None，不中断整批处理（异常隔离）。
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from langchain_core.messages import HumanMessage

from app.models.raw_news import RawNews
from app.schemas.event import ExtractedEvent
from app.services.llm import create_structured_model

logger = logging.getLogger(__name__)

# Prompt 模板路径（相对 backend/ 运行目录，与 config/ 约定一致）
_PROMPT_PATH = Path("config/prompts/event_extraction.txt")


@lru_cache
def _load_prompt_template() -> str:
    """读取并缓存事件抽取 Prompt 模板。"""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"事件抽取 Prompt 模板缺失：{_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(news: RawNews) -> str:
    """用新闻字段填充 Prompt 模板。"""
    tmpl = _load_prompt_template()
    return tmpl.format(
        title=news.title,
        summary=news.summary or "(无摘要)",
        source=news.source,
        published_at=news.published_at.isoformat() if news.published_at else "(未提供)",
    )


# 结构化模型在模块级惰性构造一次复用，避免每条新闻都重建。
_structured_model = None


def _get_structured_model():
    """惰性构造并缓存结构化 LLM（首次调用时创建）。"""
    global _structured_model
    if _structured_model is None:
        _structured_model = create_structured_model(ExtractedEvent)
    return _structured_model


def extract_event(news: RawNews) -> ExtractedEvent | None:
    """对单条新闻调用 LLM 抽取结构化事件。

    Args:
        news: 原始新闻 ORM 对象。

    Returns:
        抽取出的 ExtractedEvent；LLM 失败或异常时返回 None（已记日志）。
    """
    try:
        prompt = _build_prompt(news)
        model = _get_structured_model()
        result = model.invoke([HumanMessage(content=prompt)])
    except Exception as e:  # noqa: BLE001 - 单条隔离，吞掉所有异常不中断批次
        logger.error("抽取事件失败 news_id=%s: %s", news.id, e)
        return None

    if result is None:
        logger.warning("LLM 返回空结果 news_id=%s", news.id)
        return None

    # event_time 为空时回退到新闻发布时间
    if result.event_time is None and news.published_at is not None:
        result = result.model_copy(update={"event_time": news.published_at})

    return result


def reset_model_cache() -> None:
    """重置模块级结构化模型缓存（测试与切换 provider 时使用）。"""
    global _structured_model
    _structured_model = None
