"""JWT 鉴权体系测试：注册/登录 token、token 校验、DEV_USER_ID 回退、用户数据隔离。"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.common.auth import create_access_token, verify_token
from app.config.settings import settings

DEV_USER_ID = "00000000-0000-0000-0000-000000000000"


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SESSION_SECRET_KEY, algorithms=["HS256"])


# ---------- 注册/登录返回 token ----------

async def test_register_returns_jwt_token(client):
    resp = await client.post("/api/auth/register", json={
        "email": "auth1@test.com", "password": "pass1234", "nickname": "甲",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["token"]

    payload = _decode(data["token"])
    assert payload["sub"] == data["id"]
    assert payload["type"] == "access"
    # token 有效期 7 天
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    delta = exp - datetime.now(timezone.utc)
    assert 604799 < delta.total_seconds() < 604801  # 有效期 7 天


async def test_login_returns_token(client):
    await client.post("/api/auth/register", json={
        "email": "auth2@test.com", "password": "pass1234", "nickname": "乙",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "auth2@test.com", "password": "pass1234",
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["token"]


async def test_login_wrong_password_rejected(client):
    await client.post("/api/auth/register", json={
        "email": "auth3@test.com", "password": "pass1234", "nickname": "丙",
    })
    resp = await client.post("/api/auth/login", json={
        "email": "auth3@test.com", "password": "wrong-pass",
    })
    assert resp.status_code == 401, resp.text
    assert resp.json()["code"] == 1002  # UNAUTHORIZED


async def test_login_unknown_email_rejected(client):
    resp = await client.post("/api/auth/login", json={
        "email": "nobody@test.com", "password": "pass1234",
    })
    assert resp.status_code == 401


# ---------- JWT 工具单元测试 ----------

def test_create_and_verify_token():
    uid = uuid.uuid4()
    token = create_access_token(uid)
    assert verify_token(token) == uid


def test_verify_token_rejects_wrong_secret():
    uid = uuid.uuid4()
    forged = jwt.encode({"sub": str(uid)}, "attacker-secret", algorithm="HS256")
    assert verify_token(forged) is None


def test_verify_token_rejects_tampered_payload():
    token = create_access_token(uuid.uuid4())
    # 篡改 payload 后重签名（无密钥，直接改签名部分使其失效）
    head, _, sig = token.split(".")
    assert verify_token(f"{head}.{_b64('{\"sub\":\"11111111-1111-1111-1111-111111111111\"}')}.{sig}") is None


def _b64(s: str) -> str:
    import base64
    raw = base64.urlsafe_b64encode(s.encode()).decode().rstrip("=")
    return raw


def test_verify_token_rejects_garbage():
    assert verify_token("not-a-token") is None
    assert verify_token("") is None


# ---------- 无 token / 无效 token 回退 DEV_USER_ID ----------

async def test_no_token_uses_dev_user(client):
    """受保护端点无 token 时，数据归属 DEV_USER_ID。"""
    resp = await client.post("/api/schedule", json={
        "candidate_name": "无token候选人",
        "scheduled_at": "2027-01-01T10:00:00+00:00",
        "duration_minutes": 60,
    })
    assert resp.status_code == 200, resp.text

    day = await client.get("/api/schedule/day", params={"date": "2027-01-01"})
    events = day.json()["data"]
    assert any(e["candidate_name"] == "无token候选人" for e in events)


async def test_invalid_token_falls_back_to_dev_user(client):
    """伪造/无效 token 不会冒充身份，回退 DEV_USER_ID。"""
    forged = jwt.encode({"sub": str(uuid.uuid4())}, "attacker-secret", algorithm="HS256")
    resp = await client.post(
        "/api/schedule",
        json={"candidate_name": "伪造token", "scheduled_at": "2027-01-02T10:00:00+00:00"},
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert resp.status_code == 200, resp.text

    # 该日程归属 DEV_USER_ID：用 dev 用户视角可见
    day = await client.get("/api/schedule/day", params={"date": "2027-01-02"})
    assert any(e["candidate_name"] == "伪造token" for e in day.json()["data"])


async def test_token_user_data_isolation(client, registered_user):
    """带 token 创建的数据与 DEV_USER 数据互相隔离。"""
    headers = registered_user["headers"]

    # 用户 A 创建日程
    resp = await client.post("/api/schedule", json={
        "candidate_name": "用户A的日程",
        "scheduled_at": "2027-01-03T10:00:00+00:00",
    }, headers=headers)
    assert resp.status_code == 200, resp.text

    # 无 token（DEV_USER）看不到用户 A 的日程
    day = await client.get("/api/schedule/day", params={"date": "2027-01-03"})
    assert all(e["candidate_name"] != "用户A的日程" for e in day.json()["data"])

    # 用户 A 自己能看到
    day_a = await client.get("/api/schedule/day", params={"date": "2027-01-03"}, headers=headers)
    assert any(e["candidate_name"] == "用户A的日程" for e in day_a.json()["data"])
