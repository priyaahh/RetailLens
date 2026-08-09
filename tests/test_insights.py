"""
test_insights.py
----------------
Unit tests for InsightEngine layer verifying threshold evaluation and Insight object creation.
"""

import unittest
from unittest.mock import MagicMock
import pandas as pd

from analytics.insights import InsightEngine
from analytics.models import KPIMetric
from analytics.repository import AnalyticsRepository


class TestInsightEngine(unittest.TestCase):

    def setUp(self):
        self.mock_repo = MagicMock(spec=AnalyticsRepository)
        self.insight_engine = InsightEngine(
            repository=self.mock_repo,
            cancellation_high_threshold=5.0,
            cancellation_critical_threshold=10.0,
            top_product_concentration_threshold=20.0,
            guest_ratio_threshold=40.0,
        )

    def test_critical_cancellation_insight_trigger(self):
        """Verify cancellation rate >= 10.0% triggers CRITICAL insight."""
        kpis = {
            "cancellation_rate": KPIMetric("Cancellation Rate", 12.5, "12.5%", "CANCELLATION", "", "%"),
            "cancellation_revenue_impact": KPIMetric("Revenue Loss", 15000.0, "£15.00K", "CANCELLATION", "", "£"),
            "total_revenue": KPIMetric("Total Revenue", 100000.0, "£100.00K", "CORE", "", "£"),
            "total_customers": KPIMetric("Total Customers", 100, "100", "CORE", "", ""),
            "guest_customers": KPIMetric("Guest Customers", 10, "10", "CUSTOMER", "", ""),
        }
        self.mock_repo.get_top_products.return_value = pd.DataFrame()

        insights = self.insight_engine.generate_insights(kpis)

        self.assertTrue(any(i.severity == "CRITICAL" and i.category == "CANCELLATION" for i in insights))
        critical_insight = [i for i in insights if i.severity == "CRITICAL"][0]
        self.assertIn("12.5%", critical_insight.description)

    def test_negative_mom_revenue_growth_insight(self):
        """Verify negative revenue growth triggers HIGH severity trend contraction alert."""
        kpis = {
            "revenue_growth_pct": KPIMetric("MoM Growth", -15.4, "-15.4%", "SALES", "", "%"),
            "total_revenue": KPIMetric("Total Revenue", 85000.0, "£85.00K", "CORE", "", "£"),
            "total_customers": KPIMetric("Total Customers", 100, "100", "CORE", "", ""),
            "guest_customers": KPIMetric("Guest Customers", 10, "10", "CUSTOMER", "", ""),
        }
        self.mock_repo.get_top_products.return_value = pd.DataFrame()

        insights = self.insight_engine.generate_insights(kpis)

        self.assertTrue(any(i.category == "TREND" and i.severity == "HIGH" for i in insights))

    def test_high_guest_ratio_insight(self):
        """Verify guest customer ratio >= 40.0% triggers MEDIUM customer reliance insight."""
        kpis = {
            "total_revenue": KPIMetric("Total Revenue", 100000.0, "£100.00K", "CORE", "", "£"),
            "total_customers": KPIMetric("Total Customers", 100, "100", "CORE", "", ""),
            "guest_customers": KPIMetric("Guest Customers", 50, "50", "CUSTOMER", "", ""),  # 50%
        }
        self.mock_repo.get_top_products.return_value = pd.DataFrame()

        insights = self.insight_engine.generate_insights(kpis)

        self.assertTrue(any(i.category == "CUSTOMER" and i.severity == "MEDIUM" for i in insights))


if __name__ == "__main__":
    unittest.main()
