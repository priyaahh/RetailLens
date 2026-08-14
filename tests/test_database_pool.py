"""
test_database_pool.py
----------------------
Unit tests for database connection pooling and health checks (Phase 8 Milestone 4).
"""

import unittest
from sqlalchemy import create_engine

from database.pool import check_db_health, create_pooled_engine


class TestDatabasePool(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")

    def test_db_health_check_healthy(self):
        """Verify database health ping returns HEALTHY status."""
        health = check_db_health(self.engine)
        self.assertEqual(health["status"], "HEALTHY")
        self.assertEqual(health["database_type"], "sqlite")
        self.assertGreaterEqual(health["latency_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
