"""
test_metrics.py
----------------
Unit tests for PrometheusMetricsExporter (Phase 8 Milestone 8).
"""

import unittest
from analytics.metrics import PrometheusMetricsExporter


class TestPrometheusMetricsExporter(unittest.TestCase):

    def setUp(self):
        self.metrics = PrometheusMetricsExporter()

    def test_record_and_export_metrics(self):
        """Verify recording run/cache events and exporting Prometheus text format."""
        self.metrics.record_run(
            status="SUCCESS",
            engine="pandas",
            duration_seconds=1.5,
            rows_read=100,
            rows_inserted=90,
            rows_skipped=10,
            quality_score=95.0,
        )
        self.metrics.record_cache(hit=True)

        text_output = self.metrics.export_prometheus_text()
        self.assertIn("pipeline_runs_total 1", text_output)
        self.assertIn("rows_inserted_total 90", text_output)
        self.assertIn("cache_hits_total 1", text_output)
        self.assertIn('engine_runs_total{engine="pandas"} 1', text_output)


if __name__ == "__main__":
    unittest.main()
