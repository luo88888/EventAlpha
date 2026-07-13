"""FastAPI 鉴权依赖：从 httpOnly cookie 读 JWT 解析当前用户。

供需要登录态的端点（如 GET /api/auth/me）用 Depends(get_current_user) 注入。
现有事件/统计/采集 API 不依赖此，保持开放（仅新增登录能力）。

放在 app/api/ 而非 app/core/：依赖 FastAPI 的 Request/Depends/HTTPException，属 API 层；
app/core/security.py 保持纯函数无 FastAPI 依赖，可被批处理/测试复用。
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from utils.config_handler import load_security_config

_cookie_name = load_security_config().cookie_name


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """从请求的 httpOnly cookie 读 token，校验后返回 User ORM 对象。

    token 缺失/无效/用户不存在 → 401。
    """
    token = request.cookies.get(_cookie_name)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    username = decode_access_token(token)
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token 无效或已过期")
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    return user