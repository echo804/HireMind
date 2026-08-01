"""Redis cache helper — 为业务层提供便捷的缓存读写方法"""
import json, hashlib, logging
from app.infrastructure.redis import get_redis

logger = logging.getLogger(__name__)

DEFAULT_TTL = 300  # 5 分钟


def _cache_key(namespace: str, *parts: str) -> str:
    """生成缓存 key: hiremind:{namespace}:{part1}:{part2}..."""
    return f"hiremind:{namespace}:" + ":".join(parts)


async def cache_get(namespace: str, *parts: str):
    """从缓存读取 JSON 数据"""
    try:
        redis = get_redis()
        key = _cache_key(namespace, *parts)
        data = await redis.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Redis cache_get failed: {e}")
    return None


async def cache_set(namespace: str, *parts: str, data, ttl: int = DEFAULT_TTL):
    """将数据 JSON 序列化后写入缓存"""
    try:
        redis = get_redis()
        key = _cache_key(namespace, *parts)
        await redis.set(key, json.dumps(data, ensure_ascii=False, default=str), ex=ttl)
    except Exception as e:
        logger.warning(f"Redis cache_set failed: {e}")


async def cache_delete_pattern(pattern: str):
    """按模式删除缓存 key"""
    try:
        redis = get_redis()
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis cache_delete_pattern failed: {e}")


async def invalidate_user_cache(namespace: str, user_id: str):
    """失效某个用户在某命名空间下的所有缓存"""
    await cache_delete_pattern(f"hiremind:{namespace}:{user_id}:*")
    await cache_delete_pattern(f"hiremind:{namespace}:list:{user_id}")
    await cache_delete_pattern(f"hiremind:{namespace}:search:{user_id}:*")
