"""
test_quality_monitor.py
------------------------
Unit tests for DataQualityMonitor (Phase 6 Milestones 5 & 7).
"""

import unittest
import pandas as pd

from ingestion.loader import LoadResult
from ingestion.quality_monitor import DataQualityMonitor
from ingestion.validator import ValidationReport


class TestDataQualityMonitor(unittest.TestCase):

    def setUp(self):
        self.monitor = DataQualityMonitor(
            invalid_row_warning_threshold=5.0,
            invalid_row_critical_threshold=15.0,
        )

    def test_quality_evaluation_pass(self):
        """Verify quality evaluation calculates score and returns PASS status."""
        report = ValidationReport(total_rows=100, valid_rows=98, invalid_rows=2)
        report.finalize()

        clean_stats = {"nulls_imputed": 5, "duplicates_removed": 2, "invalid_prices_removed": 0}
        df_transformed = pd.DataFrame([
            {"IsCancellation": False, "CustomerType": "Registered"},
            {"IsCancellation": True, "CustomerType": "Guest"},
        ])
        load_res = LoadResult(rows_inserted=98, rows_skipped_duplicate=2)

        summary = self.monitor.evaluate(
            run_id="run-1",
            total_rows_read=100,
            report=report,
            clean_stats=clean_stats,
            df_transformed=df_transformed,
            load_result=load_res,
            duration_seconds=2.0,
        )

        self.assertEqual(summary.data_quality_score_pct, 98.0)
        self.assertEqual(summary.records_per_second, 50.0)
        self.assertEqual(summary.threshold_status, "PASS")
        self.assertEqual(summary.null_imputed_count, 5)

    def test_quality_evaluation_critical_alert(self):
        """Verify high invalid row rate triggers CRITICAL alert status."""
        report = ValidationReport(total_rows=100, valid_rows=80, invalid_rows=20)

        summary = self.monitor.evaluate(
            run_id="run-2",
            total_rows_read=100,
            report=report,
            duration_seconds=1.0,
        )

        self.assertEqual(summary.threshold_status, "CRITICAL")
        self.assertIn("High invalid row rate", summary.alert_messages[0])


if __name__ == "__main__":
    unittest.main()
