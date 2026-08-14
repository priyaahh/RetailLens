"""
test_run_tracker.py
--------------------
Unit tests for PipelineRunTracker (Phase 6 Milestone 2).
"""

import unittest
from datetime import datetime
from sqlalchemy import create_engine, text

from ingestion.tracker import PipelineRunTracker


class TestPipelineRunTracker(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.tracker = PipelineRunTracker(engine=self.engine)

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

    def test_start_and_complete_run(self):
        """Verify starting and completing a successful pipeline run."""
        run_id = self.tracker.start_run(
            source_file="data/raw/sales.csv",
            source_hash="abc123hash",
            watermark_before=datetime(2010, 12, 1, 0, 0),
        )
        self.assertTrue(len(run_id) > 0)

        run_data = self.tracker.get_run(run_id)
        self.assertEqual(run_data["status"], "RUNNING")
        self.assertEqual(run_data["source_hash"], "abc123hash")

        completed = self.tracker.complete_run(
            run_id=run_id,
            rows_read=100,
            rows_valid=95,
            rows_invalid=5,
            rows_transformed=95,
            rows_inserted=90,
            rows_skipped=5,
            execution_duration=1.25,
            status="SUCCESS",
        )
        self.assertTrue(completed)

        updated_run = self.tracker.get_run(run_id)
        self.assertEqual(updated_run["status"], "SUCCESS")
        self.assertEqual(updated_run["rows_inserted"], 90)
        self.assertEqual(updated_run["execution_duration"], 1.25)

    def test_fail_run(self):
        """Verify recording a failed run status and error message."""
        run_id = self.tracker.start_run(source_file="data/raw/corrupt.csv", source_hash="def456hash")
        failed = self.tracker.fail_run(run_id=run_id, error_message="Schema validation error", execution_duration=0.5)
        self.assertTrue(failed)

        run_data = self.tracker.get_run(run_id)
        self.assertEqual(run_data["status"], "FAILED")
        self.assertEqual(run_data["error_message"], "Schema validation error")


if __name__ == "__main__":
    unittest.main()
