"""鉴权接口集成测试。

覆盖 POST /api/auth/register、POST /api/auth/login、POST /api/auth/logout、GET /api/auth/me。
用 conftest 的 client + db fixtures，内存 SQLite 隔离。TestClient（httpx）默认维护
cookie jar，同 client 后续请求自动带 Set-Cookie 的 cookie。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

# ---------- 注册 ----------


def test_register_success(client):
    """注册成功：201、返回 user+token、Set-Cookie 存在。"""
    resp = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw123456", "email": "alice@example.com"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["username"] == "alice"
    assert body["user"]["email"] == "alice@example.com"
    assert body["token"]
    assert "id" in body["user"]
    assert "set-cookie" in resp.headers


def test_register_success_no_email(client):
    """不填邮箱注册成功：201、email 为 null。"""
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "password": "pw123456"},
    )
    assert resp.status_code == 201
    assert resp.json()["user"]["email"] is None


def test_register_duplicate_username(client):
    """重名注册：409、detail 含「已存在」。"""
    client.post("/api/auth/register", json={"username": "carol", "password": "pw123456"})
    resp = client.post(
        "/api/auth/register",
        json={"username": "carol", "password": "different123"},
    )
    assert resp.status_code == 409
    assert "已存在" in resp.json()["detail"]


def test_register_duplicate_email(client):
    """重复邮箱注册：409、detail 含「邮箱」。"""
    client.post(
        "/api/auth/register",
        json={"username": "dave", "password": "pw123456", "email": "dup@example.com"},
    )
    resp = client.post(
        "/api/auth/register",
        json={"username": "dave2", "password": "pw123456", "email": "dup@example.com"},
    )
    assert resp.status_code == 409
    assert "邮箱" in resp.json()["detail"]


def test_register_short_username(client):
    """用户名过短：422（Pydantic min_length）。"""
    resp = client.post("/api/auth/register", json={"username": "ab", "password": "pw123456"})
    assert resp.status_code == 422


def test_register_short_password(client):
    """密码过短：422。"""
    resp = client.post(
        "/api/auth/register", json={"username": "eve", "password": "12345"}
    )
    assert resp.status_code == 422


def test_register_username_with_space(client):
    """用户名含空白：422（field_validator）。"""
    resp = client.post(
        "/api/auth/register", json={"username": "has space", "password": "pw123456"}
    )
    assert resp.status_code == 422


# ---------- 登录 ----------


def test_login_success(client):
    """登录成功：200、返回 user、Set-Cookie。

    用新 TestClient 实例模拟未登录态（避免 register 的 cookie 干扰）。
    """
    client.post("/api/auth/register", json={"username": "frank", "password": "pw123456"})
    fresh = TestClient(app)
    resp = fresh.post(
        "/api/auth/login", json={"username": "frank", "password": "pw123456"}
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["username"] == "frank"
    assert "set-cookie" in resp.headers


def test_login_wrong_password(client):
    """密码错：401、detail == 「用户名或密码错误」。"""
    client.post("/api/auth/register", json={"username": "grace", "password": "pw123456"})
    fresh = TestClient(app)
    resp = fresh.post(
        "/api/auth/login", json={"username": "grace", "password": "wrongpass123"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "用户名或密码错误"


def test_login_nonexistent_user(client):
    """用户不存在：401、detail 与密码错一致（防枚举）。"""
    resp = client.post(
        "/api/auth/login", json={"username": "nobody", "password": "pw123456"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "用户名或密码错误"


# ---------- 获取当前用户 ----------


def test_me_after_login(client):
    """注册后同 client 调 /auth/me：200、username 正确。"""
    client.post("/api/auth/register", json={"username": "henry", "password": "pw123456"})
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "henry"


def test_me_without_login(client):
    """未登录调 /auth/me：401。"""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


# ---------- 登出 ----------


def test_logout_clears_cookie(client):
    """登出：register → logout(204) → /auth/me 401。"""
    client.post("/api/auth/register", json={"username": "ivy", "password": "pw123456"})
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 204
    # 登出后 cookie 清除，/auth/me 应 401
    me = client.get("/api/auth/me")
    assert me.status_code == 401
