"""
test_service.py
----------------
Unit tests for AnalyticsService application layer orchestration.
"""

import unittest
from unittest.mock import MagicMock
import pandas as pd

from analytics.insights import InsightEngine
from analytics.kpi_engine import KPIEngine
from analytics.models import DashboardSummary, KPIMetric
from analytics.repository import AnalyticsRepository
from analytics.service import AnalyticsService


class TestAnalyticsService(unittest.TestCase):

    def setUp(self):
        self.mock_repo = MagicMock(spec=AnalyticsRepository)
        self.mock_kpi_engine = MagicMock(spec=KPIEngine)
        self.mock_insight_engine = MagicMock(spec=InsightEngine)

        self.service = AnalyticsService(
            repository=self.mock_repo,
            kpi_engine=self.mock_kpi_engine,
            insight_engine=self.mock_insight_engine,
        )

    def test_get_dashboard_summary(self):
        """Verify get_dashboard_summary orchestrates KPIs, insights, and repository DataFrames into DashboardSummary."""
        mock_kpis = {
            "total_revenue": KPIMetric("Total Revenue", 100000.0, "£100.00K", "CORE", "", "£")
        }
        self.mock_kpi_engine.calculate_all_kpis.return_value = mock_kpis
        self.mock_insight_engine.generate_insights.return_value = []
        self.mock_repo.get_revenue_by_month.return_value = pd.DataFrame([{"period": "2010-12", "total_revenue": 100000.0}])
        self.mock_repo.get_top_products.return_value = pd.DataFrame([{"description": "ITEM 1", "total_revenue": 5000.0}])
        self.mock_repo.get_revenue_by_country.return_value = pd.DataFrame([{"country": "UK", "total_revenue": 90000.0}])
        self.mock_repo.get_customer_segments.return_value = pd.DataFrame([{"customer_type": "Registered", "total_revenue": 80000.0}])

        summary = self.service.get_dashboard_summary()

        self.assertIsInstance(summary, DashboardSummary)
        self.assertIn("total_revenue", summary.kpis)
        self.assertEqual(len(summary.revenue_trend), 1)
        self.assertEqual(len(summary.top_products), 1)

    def test_get_cancellation_analysis(self):
        """Verify get_cancellation_analysis extracts cancellation KPIs and top returned products."""
        mock_kpis = {
            "cancellation_rate": KPIMetric("Cancellation Rate", 4.7, "4.7%", "CANCELLATION", "", "%"),
            "cancellation_revenue_impact": KPIMetric("Loss", 58500.0, "£58.50K", "CANCELLATION", "", "£"),
            "cancellation_count": KPIMetric("Count", 585, "585", "CANCELLATION", "", ""),
        }
        self.mock_kpi_engine.calculate_all_kpis.return_value = mock_kpis
        self.mock_repo.get_top_products.return_value = pd.DataFrame([{"description": "RETURNED ITEM"}])

        res = self.service.get_cancellation_analysis()

        self.assertIn("cancellation_rate", res)
        self.assertEqual(res["cancellation_rate"].formatted_value, "4.7%")
        self.assertIn("top_returned_products", res)


if __name__ == "__main__":
    unittest.main()
