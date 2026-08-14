"""
cache.py
--------
Enterprise Redis & Memory Fallback Caching Layer for RetailLens (Phase 8 Milestone 5).
Provides high-performance key-value caching with TTL expiration, hit/miss metric tracking,
and zero-downtime memory fallback when Redis is absent.
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional

# Check redis library availability
HAS_REDIS = False
try:
    import redis
    HAS_REDIS = True
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class RedisCache:
    """Production Redis Caching Client with automatic local memory fallback."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Constructor connecting to Redis or initializing memory store.

        :param redis_url: Redis connection URL (e.g., 'redis://localhost:6379/0').
        """
        url = redis_url or os.getenv("REDIS_URL")
        self.client = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self.hits = 0
        self.misses = 0

        if HAS_REDIS and url:
            try:
                self.client = redis.Redis.from_url(url, decode_responses=True, socket_timeout=2)
                self.client.ping()
                logger.info("Connected to Redis cache at '%s'", url)
            except Exception as e:
                logger.warning("Redis connection failed (%s). Falling back to local memory cache.", str(e))
                self.client = None
        else:
            logger.info("Redis library/URL absent. Initialized in-memory caching fallback.")

    @property
    def is_redis_available(self) -> bool:
        """Returns True if live Redis connection is active."""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves value from cache by key.

        :param key: Cache key string.
        :return: Deserialized JSON value or None on cache miss.
        """
        if self.client:
            try:
                val = self.client.get(key)
                if val is not None:
                    self.hits += 1
                    return json.loads(val)
                self.misses += 1
                return None
            except Exception as e:
                logger.warning("Redis GET failed for key '%s': %s", key, str(e))

        # Memory Fallback GET
        item = self._memory_cache.get(key)
        if item:
            if time.time() < item["expires_at"]:
                self.hits += 1
                return item["value"]
            else:
                del self._memory_cache[key]

        self.misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """
        Stores value in cache with TTL expiration.

        :param key: Cache key string.
        :param value: Value object to cache (JSON serializable).
        :param ttl_seconds: Time-to-live expiration in seconds.
        :return: True on success.
        """
        if self.client:
            try:
                serialized = json.dumps(value)
                self.client.setex(key, ttl_seconds, serialized)
                return True
            except Exception as e:
                logger.warning("Redis SET failed for key '%s': %s", key, str(e))

        # Memory Fallback SET
        self._memory_cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds,
        }
        return True

    def delete(self, key: str) -> bool:
        """Deletes key from cache."""
        if self.client:
            try:
                self.client.delete(key)
            except Exception:
                pass
        if key in self._memory_cache:
            del self._memory_cache[key]
        return True

    def clear(self) -> bool:
        """Flushes all cached entries."""
        if self.client:
            try:
                self.client.flushdb()
            except Exception:
                pass
        self._memory_cache.clear()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Returns cache hit/miss statistics."""
        total = self.hits + self.misses
        hit_rate = round((self.hits / total) * 100, 1) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_pct": hit_rate,
            "backend": "redis" if self.is_redis_available else "memory",
        }
