"""
test_lineage.py
---------------
Unit tests for DataLineageTracker (Phase 6 Milestone 3).
"""

import unittest
from sqlalchemy import create_engine, text

from ingestion.lineage import DataLineageTracker


class TestDataLineageTracker(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.lineage_tracker = DataLineageTracker(engine=self.engine)

        with self.engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE pipeline_runs (
                    run_id TEXT PRIMARY KEY
                );
            """))
            conn.execute(text("""
                INSERT INTO pipeline_runs (run_id) VALUES ('run-123');
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

    def test_record_and_retrieve_lineage(self):
        """Verify recording and querying data lineage records."""
        recorded = self.lineage_tracker.record_lineage(
            run_id="run-123",
            source_file="data/raw/online_retail.csv",
            source_hash="hash123456",
            source_row_count=500,
            target_table="fact_sales",
            target_row_count=480,
            transformation_version="1.0.0",
        )
        self.assertTrue(recorded)

        records = self.lineage_tracker.get_lineage_by_run("run-123")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["source_file"], "data/raw/online_retail.csv")
        self.assertEqual(records[0]["target_row_count"], 480)

        file_records = self.lineage_tracker.get_lineage_for_file("data/raw/online_retail.csv")
        self.assertEqual(len(file_records), 1)


if __name__ == "__main__":
    unittest.main()
