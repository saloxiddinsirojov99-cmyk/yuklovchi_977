"""Ultra-Fast Redis Cache for file_id metadata."""

from __future__ import annotations

import json
from typing import Optional

from src.cache.redis_client import get_redis
from src.common.constants import REDIS_CACHE_PREFIX, CACHE_DEFAULT_TTL_SEC
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VideoCacheService:
    """Redis cache: video:{url_hash} → {file_id, file_size, source, cached_at}"""

    def __init__(self) -> None:
        self._redis = get_redis()
        self._ttl = CACHE_DEFAULT_TTL_SEC
        self._prefix = REDIS_CACHE_PREFIX

    def _key(self, url_hash_val: str) -> str:
        return f"{self._prefix}{url_hash_val}"

    async def get(self, url_hash_val: str) -> Optional[dict]:
        key = self._key(url_hash_val)
        try:
            data = await self._redis.get(key)
            if data is not None:
                await self._redis.expire(key, self._ttl)
                return json.loads(data)
            return None
        except Exception:
            return None

    async def get_file_id(self, url_hash_val: str) -> Optional[str]:
        data = await self.get(url_hash_val)
        return data.get("file_id") if data else None

    async def set(self, url_hash_val: str, file_id: str, **extra) -> bool:
        key = self._key(url_hash_val)
        metadata = {"file_id": file_id, **extra}
        try:
            await self._redis.setex(key, self._ttl, json.dumps(metadata))
            return True
        except Exception:
            logger.exception("Cache SET error")
            return False

    async def delete(self, url_hash_val: str) -> bool:
        key = self._key(url_hash_val)
        try:
            return await self._redis.delete(key) > 0
        except Exception:
            return False