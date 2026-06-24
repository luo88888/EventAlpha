"""应用配置：从 .env 加载，单一真相源。

所有命令一律从 backend/ 目录运行，因此 env_file="." 相对运行时 CWD 解析，
对应 backend/.env；SQLite 路径 sqlite:///./eventalpha.db 也落在 backend/ 下。
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置。新增配置项在此声明字段并给默认值。"""

    DATABASE_URL: str = "sqlite:///./eventalpha.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """返回单例 Settings，供应用与 Alembic env.py 共用。"""
    return Settings()
