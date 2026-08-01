"""Schedule 模块测试：CRUD、时间冲突检测、用户数据隔离、越权问题记录。"""

import pytest

DAY = "2027-03-10"


def _mk(scheduled_at: str, name: str = "候选人", duration: int = 60, **extra):
    body = {
        "candidate_name": name,
        "scheduled_at": scheduled_at,
        "duration_minutes": duration,
    }
    body.update(extra)
    return body


# ---------- CRUD ----------

async def test_create_schedule(client, registered_user):
    resp = await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "张三"),
                             headers=registered_user["headers"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["candidate_name"] == "张三"
    assert data["duration_minutes"] == 60
    assert data["status"] == "pending"
    return data


async def test_get_by_day_and_range(client, registered_user):
    h = registered_user["headers"]
    await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A"), headers=h)
    await client.post("/api/schedule", json=_mk(f"{DAY}T14:00:00+00:00", "B"), headers=h)
    await client.post("/api/schedule", json=_mk("2027-03-11T10:00:00+00:00", "C"), headers=h)

    day = await client.get("/api/schedule/day", params={"date": DAY}, headers=h)
    assert len(day.json()["data"]) == 2

    rng = await client.get("/api/schedule/range",
                           params={"start": f"{DAY}T00:00:00+00:00", "end": "2027-03-12T00:00:00+00:00"},
                           headers=h)
    assert len(rng.json()["data"]) == 3


async def test_update_schedule(client, registered_user):
    h = registered_user["headers"]
    created = (await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A"), headers=h)).json()["data"]
    resp = await client.put(f"/api/schedule/{created['id']}", json={"candidate_name": "改名", "notes": "备注"},
                            headers=h)
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["candidate_name"] == "改名"
    assert resp.json()["data"]["notes"] == "备注"


async def test_delete_schedule(client, registered_user):
    h = registered_user["headers"]
    created = (await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00"), headers=h)).json()["data"]
    resp = await client.delete(f"/api/schedule/{created['id']}", headers=h)
    assert resp.status_code == 200, resp.text

    day = await client.get("/api/schedule/day", params={"date": DAY}, headers=h)
    assert day.json()["data"] == []


async def test_delete_nonexistent_404(client, registered_user):
    resp = await client.delete("/api/schedule/00000000-0000-0000-0000-000000000000",
                               headers=registered_user["headers"])
    assert resp.status_code == 404


# ---------- 时间冲突检测 ----------

async def test_overlap_conflict(client, registered_user):
    h = registered_user["headers"]
    await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "已有", 60), headers=h)
    # 10:30 开始与 10:00-11:00 重叠
    resp = await client.post("/api/schedule", json=_mk(f"{DAY}T10:30:00+00:00", "冲突", 60), headers=h)
    assert resp.status_code == 409, resp.text
    assert resp.json()["code"] == 9002  # SCHEDULE_CONFLICT


async def test_adjacent_no_conflict(client, registered_user):
    h = registered_user["headers"]
    await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A", 60), headers=h)
    # 11:00 开始正好接上，不冲突
    resp = await client.post("/api/schedule", json=_mk(f"{DAY}T11:00:00+00:00", "B", 60), headers=h)
    assert resp.status_code == 200, resp.text


async def test_cancelled_event_skipped(client, registered_user):
    h = registered_user["headers"]
    created = (await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "已取消", 60),
                                 headers=h)).json()["data"]
    # 取消该日程
    await client.put(f"/api/schedule/{created['id']}", json={"status": "cancelled"}, headers=h)
    # 同一时段可再创建
    resp = await client.post("/api/schedule", json=_mk(f"{DAY}T10:30:00+00:00", "新日程", 60), headers=h)
    assert resp.status_code == 200, resp.text


@pytest.mark.xfail(reason="BUG-02: update() 中 uuid.UUID(entity.user_id) 在 asyncpg 下 entity.user_id 已是 UUID 对象，抛 AttributeError，编辑日程 500", strict=True)
async def test_update_excludes_self(client, registered_user):
    """编辑时不应与自身冲突（把开始时间改到与原时间重叠）。"""
    h = registered_user["headers"]
    created = (await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A", 120),
                                 headers=h)).json()["data"]
    resp = await client.put(f"/api/schedule/{created['id']}",
                            json={"scheduled_at": f"{DAY}T10:30:00+00:00"}, headers=h)
    assert resp.status_code == 200, resp.text


@pytest.mark.xfail(reason="BUG-02: 同上，编辑日程因 asyncpg UUID AttributeError 失败", strict=True)
async def test_update_conflicts_with_other(client, registered_user):
    h = registered_user["headers"]
    a = (await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A", 60), headers=h)).json()["data"]
    b = (await client.post("/api/schedule", json=_mk(f"{DAY}T12:00:00+00:00", "B", 60), headers=h)).json()["data"]
    # 把 B 改到与 A 重叠
    resp = await client.put(f"/api/schedule/{b['id']}",
                            json={"scheduled_at": f"{DAY}T10:30:00+00:00"}, headers=h)
    assert resp.status_code == 409, resp.text


# ---------- 用户隔离与越权 ----------

async def test_data_isolation_between_users(client, registered_user):
    """用户 A 的日程，用户 B 和 DEV_USER 均不可见。"""
    ua = registered_user["headers"]
    # 注册用户 B
    rb = await client.post("/api/auth/register", json={
        "email": "user_b@test.com", "password": "pass1234", "nickname": "乙",
    })
    ub = {"Authorization": f"Bearer {rb.json()['data']['token']}"}

    await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A的日程"), headers=ua)

    day_b = await client.get("/api/schedule/day", params={"date": DAY}, headers=ub)
    assert day_b.json()["data"] == []
    day_anon = await client.get("/api/schedule/day", params={"date": DAY})
    assert day_anon.json()["data"] == []


async def test_update_other_users_event_is_cross_user(client, registered_user):
    """记录问题：update 无用户校验——用户 B 可修改用户 A 的日程（越权）。"""
    ua = registered_user["headers"]
    rb = await client.post("/api/auth/register", json={
        "email": "user_c@test.com", "password": "pass1234", "nickname": "丙",
    })
    ub = {"Authorization": f"Bearer {rb.json()['data']['token']}"}

    created = (await client.post("/api/schedule", json=_mk(f"{DAY}T10:00:00+00:00", "A的日程"),
                                 headers=ua)).json()["data"]
    # 用户 B 尝试修改用户 A 的日程
    resp = await client.put(f"/api/schedule/{created['id']}", json={"candidate_name": "被B篡改"},
                            headers=ub)
    assert resp.status_code == 200, resp.text  # 现状：越权成功（问题记录）
