"""鉴权接口 Pydantic 模型。

- UserCreate：注册入参（username + password，email 可选）。
- UserLogin：登录入参（username + password）。
- UserOut：用户响应（脱敏，不含 password_hash）。
- TokenResponse：登录/注册成功响应（含 user 与 token；token 供调试，实际登录态靠 cookie）。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    """注册请求体。"""

    username: str = Field(min_length=3, max_length=64, description="用户名 3-64 字符")
    password: str = Field(min_length=6, max_length=128, description="密码 6-128 字符")
    email: str | None = Field(default=None, description="可选邮箱")

    @field_validator("username")
    @classmethod
    def username_no_space(cls, v: str) -> str:
        """用户名不允许含空白字符（防止首尾空格/中间空格导致登录困惑）。"""
        if any(ch.isspace() for ch in v):
            raise ValueError("用户名不能含空白字符")
        return v

    @field_validator("email")
    @classmethod
    def email_lower(cls, v: str | None) -> str | None:
        """邮箱统一小写存储，空串视为未填。"""
        if v is None:
            return None
        v = v.strip().lower()
        return v or None


class UserLogin(BaseModel):
    """登录请求体。"""

    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    """用户响应（脱敏，不含 password_hash）。"""

    id: int
    username: str
    email: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """登录/注册成功响应。

    token 字段便于前端调试与未来移动端场景；前端不读此字段存 localStorage
    （实际登录态由后端 Set-Cookie 的 httpOnly cookie 维持）。
    """

    user: UserOut
    token: str