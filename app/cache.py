import json

import redis

from app.config import settings

redis_client = redis.Redis.from_url(
    settings.redis_url,
    decode_responses=True,     # return str instead of bytes
    socket_connect_timeout=1,  # don't hang if Redis is down
    socket_timeout=1,
)

KEY_PREFIX = "url:"


def get_cached_url(short_code: str) -> dict | None:
    """Return {"id": ..., "original_url": ...} from Redis, or None on miss.

    If Redis is down we treat it as a miss, so the app keeps working
    using Postgres only.
    """
    try:
        data = redis_client.get(KEY_PREFIX + short_code)
    except redis.RedisError:
        return None
    return json.loads(data) if data else None


def set_cached_url(short_code: str, url_id: int, original_url: str) -> None:
    """Store a link in Redis with an expiry (TTL)."""
    try:
        redis_client.set(
            KEY_PREFIX + short_code,
            json.dumps({"id": url_id, "original_url": original_url}),
            ex=settings.cache_ttl_seconds,
        )
    except redis.RedisError:
        pass  # caching is an optimisation; failing to cache is not an error


def is_available() -> bool:
    """True if Redis responds to PING."""
    try:
        return bool(redis_client.ping())
    except redis.RedisError:
        return False