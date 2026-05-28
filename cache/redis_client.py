import redis


def get_redis(redis_url: str) -> redis.Redis:
    return redis.Redis.from_url(redis_url)
