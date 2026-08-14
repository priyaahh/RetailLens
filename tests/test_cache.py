"""
test_cache.py
-------------
Unit tests for RedisCache and memory fallback caching (Phase 8 Milestone 5).
"""

import unittest
from analytics.cache import RedisCache


class TestRedisCache(unittest.TestCase):

    def setUp(self):
        self.cache = RedisCache()  # Local memory fallback mode

    def test_cache_set_get_delete_stats(self):
        """Verify caching set, get, delete, hit/miss tracking, and stats."""
        key = "kpi_summary_test"
        val = {"total_revenue": 45.30, "total_orders": 2}

        # 1. Miss initially
        self.assertIsNone(self.cache.get(key))

        # 2. Set
        self.assertTrue(self.cache.set(key, val, ttl_seconds=300))

        # 3. Hit
        res = self.cache.get(key)
        self.assertEqual(res["total_revenue"], 45.30)

        # 4. Check Stats
        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)

        # 5. Delete
        self.cache.delete(key)
        self.assertIsNone(self.cache.get(key))


if __name__ == "__main__":
    unittest.main()
