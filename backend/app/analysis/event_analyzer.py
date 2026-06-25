"""事件分析器：单个 Event → LLM 投资影响分析 → AnalyzedEvent。

模式对齐 processors/event_extractor.py：
- Prompt 模板外置于 config/prompts/event_analysis.txt，启动时读取一次并缓存。
- 通过 create_structured_model(AnalyzedEvent) 让 LLM 直接产出 schema 实例。
- 单条分析失败时记日志返回 None，不中断整批处理（异常隔离）。
- 遇到限流（HTTP 429）自动指数退避重试，最多 max_retries 次。
"""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from pathlib import Path

from langchain_core.messages import HumanMessage

from app.models.event import Event
from app.schemas.event import AnalyzedEvent
from app.services.llm import create_structured_model

logger = logging.getLogger(__name__)

# Prompt 模板路径（相对 backend/ 运行目录）
_PROMPT_PATH = Path("config/prompts/event_analysis.txt")

# 重试配置
_MAX_RETRIES = 3
_BASE_DELAY = 2  # 秒，指数退避基数


@lru_cache
def _load_prompt_template() -> str:
    """读取并缓存事件分析 Prompt 模板。"""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"事件分析 Prompt 模板缺失：{_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(event: Event) -> str:
    """用事件字段填充 Prompt 模板。"""
    tmpl = _load_prompt_template()
    return tmpl.format(
        event_title=event.event_title,
        event_type=event.event_type,
        event_subject=event.event_subject or "(未指定)",
        summary=event.summary or "(无摘要)",
    )


def _is_rate_limit_error(exc: Exception) -> bool:
    """判断异常是否为限流（HTTP 429）。"""
    msg = str(exc).lower()
    return "429" in msg or "rate" in msg or "limit" in msg or "限流" in msg


# 结构化模型在模块级惰性构造一次复用，避免每次都重建。
_structured_model = None


def _get_structured_model():
    """惰性构造并缓存结构化 LLM（首次调用时创建）。"""
    global _structured_model
    if _structured_model is None:
        _structured_model = create_structured_model(AnalyzedEvent)
    return _structured_model


def analyze_event(event: Event, max_retries: int = _MAX_RETRIES) -> AnalyzedEvent | None:
    """对单个事件调用 LLM 生成投资影响分析。

    遇到限流时自动指数退避重试，其他异常直接返回 None。

    Args:
        event: 事件 ORM 对象。
        max_retries: 限流最大重试次数。

    Returns:
        分析结果 AnalyzedEvent；LLM 失败或异常时返回 None（已记日志）。
    """
    prompt = _build_prompt(event)
    model = _get_structured_model()

    for attempt in range(max_retries + 1):
        try:
            result = model.invoke([HumanMessage(content=prompt)])
            return result
        except Exception as e:  # noqa: BLE001
            if _is_rate_limit_error(e) and attempt < max_retries:
                delay = _BASE_DELAY * (2 ** attempt)
                logger.warning(
                    "限流 event_id=%s，%ds 后重试 (%d/%d)",
                    event.id, delay, attempt + 1, max_retries,
                )
                time.sleep(delay)
                continue
            logger.error("分析事件失败 event_id=%s: %s", event.id, e)
            return None

    return None


def reset_model_cache() -> None:
    """重置模块级结构化模型缓存（测试与切换 provider 时使用）。"""
    global _structured_model
    _structured_model = None
