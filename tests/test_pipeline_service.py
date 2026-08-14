"""
test_pipeline_service.py
-------------------------
Unit tests for PipelineMonitoringService and PipelineMonitoringRepository (Phase 6 Milestone 9).
"""

import unittest
from sqlalchemy import create_engine, text

from analytics.pipeline_repository import PipelineMonitoringRepository
from analytics.pipeline_service import PipelineMonitoringService


class TestPipelineMonitoringService(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.repo = PipelineMonitoringRepository(engine=self.engine)
        self.service = PipelineMonitoringService(repository=self.repo)

        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE pipeline_runs (
                    run_id TEXT PRIMARY KEY,
                    pipeline_name TEXT NOT NULL DEFAULT 'RetailLens_ETL',
                    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    status TEXT NOT NULL DEFAULT 'RUNNING',
                    source_file TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    rows_read INTEGER NOT NULL DEFAULT 0,
                    rows_valid INTEGER NOT NULL DEFAULT 0,
                    rows_invalid INTEGER NOT NULL DEFAULT 0,
                    rows_transformed INTEGER NOT NULL DEFAULT 0,
                    rows_inserted INTEGER NOT NULL DEFAULT 0,
                    rows_skipped INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    execution_duration REAL DEFAULT 0.0,
                    watermark_before TIMESTAMP,
                    watermark_after TIMESTAMP
                );
            """))

            conn.execute(text("""
                CREATE TABLE data_lineage (
                    lineage_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    source_file TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    source_row_count INTEGER NOT NULL DEFAULT 0,
                    target_table TEXT NOT NULL DEFAULT 'fact_sales',
                    target_row_count INTEGER NOT NULL DEFAULT 0,
                    transformation_version TEXT NOT NULL DEFAULT '1.0.0',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

            conn.execute(text("""
                INSERT INTO pipeline_runs (
                    run_id, pipeline_name, started_at, completed_at, status, source_file, source_hash,
                    rows_read, rows_valid, rows_invalid, rows_transformed, rows_inserted, rows_skipped, execution_duration
                ) VALUES 
                ('run-1', 'fact_sales', '2026-08-14 10:00:00', '2026-08-14 10:00:02', 'SUCCESS', 'sales1.csv', 'hash1', 100, 95, 5, 95, 95, 0, 2.0),
                ('run-2', 'fact_sales', '2026-08-14 11:00:00', '2026-08-14 11:00:01', 'FAILED', 'sales2.csv', 'hash2', 50, 0, 50, 0, 0, 0, 1.0);
            """))

    def test_get_latest_run(self):
        """Verify fetching latest run record."""
        latest = self.service.get_latest_run()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["run_id"], "run-2")

    def test_get_failed_runs(self):
        """Verify fetching failed runs."""
        failed_df = self.service.get_failed_runs()
        self.assertEqual(len(failed_df), 1)
        self.assertEqual(failed_df.iloc[0]["run_id"], "run-2")

    def test_get_pipeline_health_status(self):
        """Verify calculating overall pipeline health status."""
        health = self.service.get_pipeline_health_status()
        self.assertEqual(health["total_runs"], 2)
        self.assertEqual(health["failed_runs"], 1)
        self.assertEqual(health["success_rate_pct"], 50.0)
        self.assertEqual(health["health_status"], "CRITICAL")


if __name__ == "__main__":
    unittest.main()
