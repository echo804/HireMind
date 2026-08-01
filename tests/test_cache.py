"""Redis 缓存工具测试：cache_get/cache_set/invalidate_user_cache。"""

import uuid

from app.infrastructure.cache import (
    cache_delete_pattern, cache_get, cache_set, invalidate_user_cache,
)


async def test_set_get_roundtrip():
    await cache_set("test", "k", "v1", data={"a": 1, "b": [1, 2]})
    assert await cache_get("test", "k", "v1") == {"a": 1, "b": [1, 2]}


async def test_get_miss_returns_none():
    assert await cache_get("test", "nope", uuid.uuid4().hex) is None


async def test_set_overwrites():
    await cache_set("test", "ow", data="first")
    await cache_set("test", "ow", data="second")
    assert await cache_get("test", "ow") == "second"


async def test_set_with_ttl():
    await cache_set("test", "ttl", data="x", ttl=1)
    import asyncio
    await asyncio.sleep(1.2)
    assert await cache_get("test", "ttl") is None


async def test_delete_pattern():
    await cache_set("test", "del", "a", data=1)
    await cache_set("test", "del", "b", data=2)
    await cache_delete_pattern("hiremind:test:del:*")
    assert await cache_get("test", "del", "a") is None
    assert await cache_get("test", "del", "b") is None


async def test_invalidate_user_cache():
    uid = uuid.uuid4().hex
    # list 缓存 key: hiremind:{ns}:list:{uid}
    await cache_set("kb", "list", uid, data=[{"id": 1}])
    # 带前缀的其他 key
    await cache_set("kb", uid, "doc", data="x")
    await invalidate_user_cache("kb", uid)

    assert await cache_get("kb", "list", uid) is None
    assert await cache_get("kb", uid, "doc") is None
