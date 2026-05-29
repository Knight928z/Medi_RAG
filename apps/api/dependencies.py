from typing import AsyncGenerator

from cache.redis_client import get_redis
from core.config import get_settings
from storage.database import get_async_session


async def get_db_session() -> AsyncGenerator:
    settings = get_settings()
    async with get_async_session(settings.database_url) as session:
        yield session


def get_redis_client():
    settings = get_settings()
    return get_redis(settings.redis_url)
