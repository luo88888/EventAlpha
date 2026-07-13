"""鉴权接口：

- POST /api/auth/register：注册（username + password，email 可选），成功后 Set-Cookie 自动登录。
- POST /api/auth/login：用户名 + 密码登录，Set-Cookie。
- POST /api/auth/logout：清除 cookie。
- GET /api/auth/me：返回当前登录用户（从 cookie 读 token）。

仅新增登录能力：现有事件/统计/采集 API 保持开放，不依赖本模块。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut
from utils.config_handler import load_security_config

router = APIRouter()
_cfg = load_security_config()


def _set_auth_cookie(response: Response, token: str) -> None:
    """统一设置 httpOnly auth cookie。

    httponly 硬编码为 True（安全约束不可配，防 JS 读 token）；其余参数走 security.yaml。
    """
    response.set_cookie(
        key=_cfg.cookie_name,
        value=token,
        max_age=_cfg.cookie_max_age,
        path=_cfg.cookie_path,
        httponly=True,
        secure=_cfg.cookie_secure,
        samesite=_cfg.cookie_samesite,
    )


def _clear_auth_cookie(response: Response) -> None:
    """清除 auth cookie。"""
    response.delete_cookie(key=_cfg.cookie_name, path=_cfg.cookie_path)


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate, response: Response, db: Session = Depends(get_db)
) -> TokenResponse:
    """注册新用户。username 唯一，email 若填则唯一。

    成功后直接 Set-Cookie 自动登录，返回 TokenResponse（含 user + token）。
    """
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    if payload.email and db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已被注册")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        email=payload.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.username)
    _set_auth_cookie(response, token)
    return TokenResponse(user=UserOut.model_validate(user), token=token)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    """用户名 + 密码登录。成功 Set-Cookie，返回 TokenResponse。

    密码错与用户不存在统一返回 401「用户名或密码错误」，防止用户名枚举。
    """
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token(user.username)
    _set_auth_cookie(response, token)
    return TokenResponse(user=UserOut.model_validate(user), token=token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    """登出：清除 auth cookie。无数据库操作。"""
    _clear_auth_cookie(response)


@router.get("/auth/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """返回当前登录用户。未登录（无 cookie / token 无效）→ 401。"""
    return UserOut.model_validate(current_user)