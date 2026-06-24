"""LLM 模型工厂包。

对外暴露 create_model / create_structured_model 两个入口，支持
deepseek、qwen、openai 三类提供方，通过 (provider, model_name) 确定。
"""

from __future__ import annotations

from app.services.llm.factory import create_model, create_structured_model

__all__ = ["create_model", "create_structured_model"]
