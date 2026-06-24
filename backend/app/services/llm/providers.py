"""各提供方的对话模型构造器。

统一入口 build_chat_model(provider, model_name, **kwargs)：
- deepseek -> langchain_deepseek.ChatDeepSeek（API Key 自动读 DEEPSEEK_API_KEY）
- qwen     -> langchain_community.chat_models.tongyi.ChatTongyi（API Key 自动读 DASHSCOPE_API_KEY）
- openai   -> langchain_openai.ChatOpenAI（API Key 自动读 OPENAI_API_KEY）

API Key 由底层 SDK 从对应环境变量自动读取，无需在此显式传参；
环境变量在启动前由 utils.config_handler 从 .env 注入。

Qwen 不在 init_chat_model 的内置 provider 注册表中，故直接实例化 ChatTongyi
（与项目既有 Qwen 用法一致）。
"""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

SUPPORTED_PROVIDERS = ("deepseek", "qwen", "openai")


def _build_deepseek(model_name: str, **kwargs: Any) -> BaseChatModel:
    from langchain_deepseek import ChatDeepSeek

    return ChatDeepSeek(model=model_name, **kwargs)


def _build_qwen(model_name: str, **kwargs: Any) -> BaseChatModel:
    from langchain_community.chat_models.tongyi import ChatTongyi

    return ChatTongyi(model=model_name, **kwargs)


def _build_openai(model_name: str, **kwargs: Any) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=model_name, **kwargs)


_BUILDERS = {
    "deepseek": _build_deepseek,
    "qwen": _build_qwen,
    "openai": _build_openai,
}


def build_chat_model(provider: str, model_name: str, **kwargs: Any) -> BaseChatModel:
    """按提供方创建对话模型。

    Args:
        provider: 提供方标识（deepseek / qwen / openai）。
        model_name: 模型名称。
        **kwargs: 透传给底层 chat model 的额外参数。

    Returns:
        BaseChatModel 实例。

    Raises:
        ValueError: provider 不在支持列表中。
    """
    builder = _BUILDERS.get(provider)
    if builder is None:
        raise ValueError(
            f"不支持的 LLM 提供方：{provider!r}，可选：{', '.join(SUPPORTED_PROVIDERS)}"
        )
    return builder(model_name, **kwargs)
