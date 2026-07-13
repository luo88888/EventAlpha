"""users：用户表（鉴权层产物）。

username 唯一，作为登录标识。password_hash 存 bcrypt 哈希，不存明文。
email 可选（注册可不填），有则唯一（SQLite/PG 的 UNIQUE 允许多个 NULL）。
登录用 username + password。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 登录标识，唯一，建索引便于登录查询
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # bcrypt 哈希（对超 72 字节密码先 SHA-256 派生再 bcrypt 编码），不存明文
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # 可选邮箱：填则唯一（SQLite UNIQUE 允许多个 NULL，符合不填不查重）
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=utcnow)