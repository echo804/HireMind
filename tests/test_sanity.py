"""基础设施冒烟：客户端、建表、注册、健康检查。"""


async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_register_login_flow(client):
    resp = await client.post("/api/auth/register", json={
        "email": "sanity@test.com", "password": "pass1234", "nickname": "sanity",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["token"]

    login = await client.post("/api/auth/login", json={
        "email": "sanity@test.com", "password": "pass1234",
    })
    assert login.status_code == 200, login.text
    assert login.json()["data"]["token"]


async def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "password": "pass1234", "nickname": "dup"}
    r1 = await client.post("/api/auth/register", json=payload)
    r2 = await client.post("/api/auth/register", json=payload)
    assert r1.status_code == 200
    assert r2.status_code != 200
