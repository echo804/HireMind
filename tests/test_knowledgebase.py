"""知识库测试：上传/列表/搜索/删除、鉴权隔离、缓存命中与失效（记录 search 缓存失效问题）。"""

import hashlib

import pytest

from app.infrastructure.cache import cache_get

TXT = "这是第一段知识内容。这是第二句补充说明。\n\n这是第二段，关于 React 的虚拟 DOM 原理与性能优化。"


async def _upload(client, headers, name="test.txt", content=TXT, ftype="text/plain"):
    if isinstance(content, str):
        content = content.encode("utf-8")
    resp = await client.post("/api/knowledge/upload",
                             files={"file": (name, content, ftype)},
                             headers=headers)
    return resp


async def test_upload_txt_success(client, registered_user, mock_ai):
    resp = await _upload(client, registered_user["headers"])
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["filename"] == "test.txt"
    assert data["status"] == "ready"
    assert data["chunk_count"] > 0


async def test_upload_unsupported_type(client, registered_user, mock_ai):
    resp = await _upload(client, registered_user["headers"], name="evil.exe",
                         content=b"MZ", ftype="application/octet-stream")
    assert resp.status_code == 400


async def test_upload_empty_text(client, registered_user, mock_ai):
    resp = await _upload(client, registered_user["headers"], name="empty.md", content="  \n  ")
    assert resp.status_code == 400


@pytest.mark.xfail(reason="BUG-01: cache_set 的 data 为 keyword-only 参数，list_documents 位置传参导致 TypeError，列表缓存路径 500", strict=True)
async def test_list_and_get_content(client, registered_user, mock_ai):
    h = registered_user["headers"]
    doc = (await _upload(client, h)).json()["data"]

    lst = await client.get("/api/knowledge", headers=h)
    assert lst.status_code == 200
    assert any(d["id"] == doc["id"] for d in lst.json()["data"])

    content = await client.get(f"/api/knowledge/{doc['id']}/content", headers=h)
    assert content.status_code == 200
    assert content.json()["data"]["chunks"]


@pytest.mark.xfail(reason="BUG-03: kb search 向量参数以字符串传给 <=> bind param，asyncpg 下 PostgresSyntaxError，搜索不可用", strict=True)
async def test_search_returns_chunks(client, registered_user, mock_ai):
    h = registered_user["headers"]
    await _upload(client, h, content=TXT * 5)
    resp = await client.post("/api/knowledge/search", json={"query": "React 虚拟 DOM", "top_k": 3},
                             headers=h)
    assert resp.status_code == 200, resp.text
    results = resp.json()["data"]
    assert len(results) > 0
    assert "score" in results[0] and "content" in results[0]


@pytest.mark.xfail(reason="BUG-01: cache_set 位置传参导致 list_documents 500，无法验证用户隔离", strict=True)
async def test_data_isolation(client, registered_user, mock_ai):
    """用户 A 上传的文档，用户 B 与匿名用户不可见。"""
    h = registered_user["headers"]
    await _upload(client, h, name="a.txt")

    rb = await client.post("/api/auth/register", json={
        "email": "kb_b@test.com", "password": "pass1234", "nickname": "乙",
    })
    hb = {"Authorization": f"Bearer {rb.json()['data']['token']}"}

    lst_b = await client.get("/api/knowledge", headers=hb)
    assert lst_b.json()["data"] == []
    lst_anon = await client.get("/api/knowledge")
    assert lst_anon.json()["data"] == []


@pytest.mark.xfail(reason="BUG-01: cache_set 位置传参导致列表缓存路径 500，删除后列表接口本身失败", strict=True)
async def test_delete_invalidates_list_cache(client, registered_user, mock_ai):
    """删除文档后列表缓存应失效（invalidate_user_cache）。"""
    h = registered_user["headers"]
    doc = (await _upload(client, h)).json()["data"]

    # 首次 list 写入缓存
    lst = await client.get("/api/knowledge", headers=h)
    assert any(d["id"] == doc["id"] for d in lst.json()["data"])

    # 删除后 list 不应再包含
    resp = await client.delete(f"/api/knowledge/{doc['id']}", headers=h)
    assert resp.status_code == 200, resp.text

    lst2 = await client.get("/api/knowledge", headers=h)
    assert all(d["id"] != doc["id"] for d in lst2.json()["data"])


@pytest.mark.xfail(reason="BUG-01/03: search 路径 cache_set 位置传参 + 向量 SQL 语法错误，无法验证缓存失效行为（另见 BUG-04 缓存 key 不含 user_id）", strict=True)
async def test_search_cache_not_invalidated_on_delete(client, registered_user, mock_ai):
    """记录问题：search 缓存 key 不带 user_id 前缀，删除文档后不会失效（现状断言）。"""
    h = registered_user["headers"]
    uid = registered_user["id"]
    doc = (await _upload(client, h, name="del.txt", content="缓存失效测试内容" * 20)).json()["data"]

    # 首次搜索写入缓存
    r1 = await client.post("/api/knowledge/search", json={"query": "缓存失效测试", "top_k": 3}, headers=h)
    assert r1.status_code == 200
    qh = hashlib.md5(f"缓存失效测试:{uid}:3".encode()).hexdigest()[:12]
    assert await cache_get("kb", "search", qh) is not None

    # 删除文档
    await client.delete(f"/api/knowledge/{doc['id']}", headers=h)

    # 现状：search 缓存仍在（不会被 invalidate_user_cache 清除）→ 记录为问题
    assert await cache_get("kb", "search", qh) is not None
