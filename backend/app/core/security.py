"""鉴权安全工具：密码哈希（bcrypt）+ JWT 签发/校验。

密码用 bcrypt 原生包（4.x+，无需 passlib 封装）。bcrypt 单次哈希上限 72 字节，
对超长密码先做 SHA-256 派生 + base64 编码再喂入 bcrypt，解除长度限制同时保留工作量。
JWT 用 PyJWT（HS256）。SECRET_KEY 从 .env 经 load_security_config() 间接触发
_ensure_dotenv() 注入 os.environ。

纯函数无 FastAPI 依赖，便于测试与批处理复用。
"""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from utils.config_handler import load_security_config

_security_cfg = load_security_config()


def _bcrypt_digest(password: str) -> bytes:
    """对密码做 bcrypt 摘要（含随机 salt），返回 bytes 形式的哈希。

    对超 72 字节的密码先 SHA-256+base64 派生再 bcrypt，规避 bcrypt 的 72 字节上限。
    """
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = base64.b64encode(hashlib.sha256(pw_bytes).digest())
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12))


def hash_password(plain: str) -> str:
    """明文密码 → bcrypt 哈希字符串（含 salt）。入库存此字符串。"""
    return _bcrypt_digest(plain).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文与哈希是否匹配。不匹配或哈希格式异常返回 False。

    bcrypt.checkpw 内部用常量时间比较，无需再包 hmac.compare_digest（后者不接受 bool）。
    """
    pw_bytes = plain.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = base64.b64encode(hashlib.sha256(pw_bytes).digest())
    try:
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(subject: str) -> str:
    """签发 JWT。subject 为 username（登录标识）。

    Raises:
        RuntimeError: SECRET_KEY 未配置。应在启动期或首次签发时尽早暴露配置错误。
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "exp": now + timedelta(minutes=_security_cfg.access_token_expire_minutes),
        "iat": now,
    }
    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        raise RuntimeError("SECRET_KEY 未配置，请在 .env 中设置")
    return jwt.encode(payload, secret, algorithm=_security_cfg.algorithm)


def decode_access_token(token: str) -> str | None:
    """校验并解码 JWT，返回 username（sub）。token 无效/过期返回 None。

    不抛异常：调用方（get_current_user 依赖）根据 None 决定 401，避免运行期崩溃。
    """
    secret = os.environ.get("SECRET_KEY", "")
    if not secret:
        return None
    try:
        payload = jwt.decode(token, secret, algorithms=[_security_cfg.algorithm])
    except jwt.PyJWTError:
        return None
    sub: str | None = payload.get("sub")
    return sub