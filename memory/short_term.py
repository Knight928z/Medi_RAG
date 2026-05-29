from __future__ import annotations

from typing import Any, Dict, Optional

import redis

from cache.redis_client import get_json, set_json


class ShortTermWorkflowMemory:
    """Redis-backed current-session memory with explicit TTL."""

    def __init__(self, client: redis.Redis, ttl_seconds: int):
        self.client = client
        self.ttl_seconds = ttl_seconds

    @staticmethod
    def key(request_id: str) -> str:
        return f"memory:session:{request_id}"

    def get(self, request_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not request_id:
            return None
        value = get_json(self.client, self.key(request_id))
        return value if isinstance(value, dict) else None

    def set(self, request_id: str, state: Dict[str, Any]) -> None:
        set_json(self.client, self.key(request_id), state, ttl_seconds=self.ttl_seconds)

    def touch(self, request_id: str) -> None:
        self.client.expire(self.key(request_id), self.ttl_seconds)
