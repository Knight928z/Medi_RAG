from typing import Any, Optional

import orjson
import redis


def get_redis(redis_url: str) -> redis.Redis:
    return redis.Redis.from_url(redis_url)


def set_json(client: redis.Redis, key: str, payload: Any, ttl_seconds: Optional[int] = None) -> None:
    data = orjson.dumps(payload)
    if ttl_seconds:
        client.setex(key, ttl_seconds, data)
    else:
        client.set(key, data)


def get_json(client: redis.Redis, key: str) -> Optional[Any]:
    raw = client.get(key)
    if raw is None:
        return None
    return orjson.loads(raw)
