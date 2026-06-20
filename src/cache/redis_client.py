"""Redis Client — Cloud Redis (Upstash) compatible. No AUTH if no password."""

from __future__ import annotations

from typing import Optional
import redis.asyncio as aioredis
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
_redis: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _redis
    if _redis is not None:
        return
    _redis = aioredis.Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=10,
        retry_on_timeout=True,
        health_check_interval=30,
        max_connections=50,
    )
    await _redis.ping()
    logger.info("Redis connected")


async def close_redis() -> None:
    global _redis
    if _redis is None:
        return
    await _redis.aclose()
    _redis = None


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


async def health_check() -> bool:
    try:
        await get_redis().ping()
        return True
    except Exception:
        return False