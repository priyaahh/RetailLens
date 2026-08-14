"""
test_api.py
-----------
Unit tests for RetailLensAPI REST service boundary (Phase 8 Milestone 6).
"""

import unittest
from unittest.mock import MagicMock

import pandas as pd

from api.app import RetailLensAPI


class TestRetailLensAPI(unittest.TestCase):

    def setUp(self):
        self.mock_analytics = MagicMock()
        self.mock_monitoring = MagicMock()

        self.mock_analytics.kpi_engine.get_all_kpis.return_value = {"total_revenue": 100.0}
        self.mock_monitoring.get_recent_runs.return_value = pd.DataFrame([
            {"run_id": "run-1", "status": "SUCCESS"}
        ])
        self.mock_monitoring.get_run.return_value = {"run_id": "run-1", "status": "SUCCESS"}

        self.api = RetailLensAPI(
            analytics_service=self.mock_analytics,
            monitoring_service=self.mock_monitoring,
        )

    def test_health_endpoint(self):
        """Verify GET /health liveness probe."""
        code, body = self.api.handle_request("/health")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "HEALTHY")

    def test_ready_endpoint(self):
        """Verify GET /ready readiness probe."""
        code, body = self.api.handle_request("/ready")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "READY")

    def test_pipeline_runs_endpoint(self):
        """Verify GET /pipeline/runs endpoint."""
        code, body = self.api.handle_request("/pipeline/runs")
        self.assertEqual(code, 200)
        self.assertEqual(body["count"], 1)

    def test_kpis_endpoint(self):
        """Verify GET /analytics/kpis endpoint."""
        code, body = self.api.handle_request("/analytics/kpis")
        self.assertEqual(code, 200)
        self.assertEqual(body["data"]["total_revenue"], 100.0)


if __name__ == "__main__":
    unittest.main()
