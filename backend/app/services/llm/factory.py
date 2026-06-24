"""LLM 模型工厂。

对外暴露两个入口：
- create_model：按 (provider, model_name) 创建对话模型（BaseChatModel）。
- create_structured_model：在 create_model 基础上调用 chat_model.with_structured_output()，
  得到「输入消息 -> 给定类型实例」的 Runnable，用于让 LLM 产出符合 schema 的结构化结果。

支持三个提供方：deepseek、qwen、openai。provider 与 model_name 任一缺省时
取 config/llm.yaml 中的默认值（默认提供方 deepseek，默认模型 deepseek-v4-flash）。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

from utils.config_handler import load_llm_config
from app.services.llm.providers import build_chat_model


def create_model(
    model_name: str | None = None,
    provider: str | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    """创建对话模型。

    Args:
        model_name: 模型名称；缺省取 load_llm_config().default_model。
        provider: 模型提供方（deepseek / qwen / openai）；缺省取 load_llm_config().default_provider。
        **kwargs: 透传给底层 chat model 的额外参数（temperature、max_tokens 等）。

    Returns:
        BaseChatModel 实例。
    """
    settings = load_llm_config()
    provider = (provider or settings.default_provider).strip().lower()
    model_name = (model_name or settings.default_model).strip()
    return build_chat_model(provider=provider, model_name=model_name, **kwargs)


def create_structured_model[T: BaseModel](
    schema: type[T],
    model_name: str | None = None,
    provider: str | None = None,
    **kwargs: Any,
) -> Any:
    """创建带结构化输出的对话模型。

    通过 chat_model.with_structured_output(schema) 包装，返回的 Runnable 直接
    产出 schema 实例（pydantic model 或 TypedDict），而非自然语言文本。

    Args:
        schema: 目标结构类型（pydantic BaseModel 子类或 TypedDict）。
        model_name: 模型名称；缺省取 load_llm_config().default_model。
        provider: 模型提供方；缺省取 load_llm_config().default_provider。
        **kwargs: 透传给底层 chat model 的额外参数。

    Returns:
        with_structured_output 包装后的 Runnable（输入消息 -> schema 实例）。
    """
    chat_model = create_model(model_name=model_name, provider=provider, **kwargs)
    return chat_model.with_structured_output(schema)


if __name__ == "__main__":
    print(create_model(model_name="gpt-5.4-nano"))