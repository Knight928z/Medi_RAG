from typing import Generator

from cache.redis_client import get_redis
from core.config import get_settings
from storage.database import get_session


def get_db_session() -> Generator:
    settings = get_settings()
    yield from get_session(settings.database_url)


def get_redis_client():
    settings = get_settings()
    return get_redis(settings.redis_url)
