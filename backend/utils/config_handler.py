"""配置加载工具。

从 config/ 目录加载各模块 YAML 配置文件，提供类型安全的配置对象访问。

设计原则：
- 每个业务模块对应一个独立的 YAML 文件（llm.yaml、rag.yaml、database.yaml …）
- 通过 @lru_cache 缓存，多次调用返回同一实例
- .env 在首次加载配置时自动载入，确保 API Key 等环境变量就绪
- 扩展方式：新增 YAML 文件 + 对应 dataclass + load_*_config() 函数即可

所有命令从 backend/ 目录运行，因此 config/ 与 .env 均相对运行时 CWD 解析。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

# ── 内部工具 ──────────────────────────────────────────────

_CONFIG_DIR = Path("config")
_DOTENV_PATH = Path(".env")


def _ensure_dotenv() -> None:
    """加载 .env 文件中的环境变量（已存在的环境变量会被覆盖）。"""
    if not _DOTENV_PATH.exists():
        return
    from dotenv import load_dotenv

    load_dotenv(_DOTENV_PATH, override=True)


def _load_yaml(filename: str) -> dict[str, Any]:
    """读取 config/{filename} 并返回解析后的字典。

    Args:
        filename: YAML 文件名（如 "llm.yaml"）。

    Returns:
        解析后的字典；文件缺失时返回空字典（回退到 dataclass 默认值）。

    Raises:
        ValueError: 文件存在但顶层不是映射类型。
    """
    _ensure_dotenv()
    filepath = _CONFIG_DIR / filename
    if not filepath.exists():
        return {}
    with filepath.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{filepath} 顶层应为映射（dict），实际为 {type(data).__name__}")
    return data


def _build_config[T](cls: type[T], data: dict[str, Any]) -> T:
    """用 YAML 数据填充 dataclass，仅传入 dataclass 已定义的字段（忽略 YAML 中的未知键）。"""
    valid_keys = set(cls.__dataclass_fields__.keys())  # type: ignore[union-attr]
    return cls(**{k: v for k, v in data.items() if k in valid_keys})


# ── 配置模型 ──────────────────────────────────────────────


@dataclass(frozen=True)
class LLMConfig:
    """LLM 模型工厂默认值。API Key 由 .env 注入，不在此处。"""

    default_provider: str = "deepseek"
    default_model: str = "deepseek-v4-flash"


@dataclass(frozen=True)
class DatabaseConfig:
    """数据库连接配置。"""

    url: str = "sqlite:///./eventalpha.db"


@dataclass(frozen=True)
class RAGConfig:
    """RAG 检索增强生成配置。"""

    embedding_model: str = ""
    vector_store_type: str = "chroma"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k: int = 5


# ── 公开加载函数 ───────────────────────────────────────────


@lru_cache
def load_llm_config() -> LLMConfig:
    """加载 LLM 配置（默认 provider、model 等）。"""
    return _build_config(LLMConfig, _load_yaml("llm.yaml"))


@lru_cache
def load_rag_config() -> RAGConfig:
    """加载 RAG 配置（向量库、嵌入模型、检索参数等）。"""
    return _build_config(RAGConfig, _load_yaml("rag.yaml"))


@lru_cache
def load_database_config() -> DatabaseConfig:
    """加载数据库配置（连接 URL 等）。"""
    return _build_config(DatabaseConfig, _load_yaml("database.yaml"))
