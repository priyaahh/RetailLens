"""
test_kpi_engine.py
-------------------
Unit tests for KPIEngine layer using mocked repository outputs.
"""

import unittest
from unittest.mock import MagicMock
import pandas as pd

from analytics.kpi_engine import KPIEngine
from analytics.repository import AnalyticsRepository


class TestKPIEngine(unittest.TestCase):

    def setUp(self):
        self.mock_repo = MagicMock(spec=AnalyticsRepository)
        self.kpi_engine = KPIEngine(repository=self.mock_repo)

    def test_calculate_all_kpis_empty(self):
        """Verify KPIEngine safely formats zero metrics when repository returns empty values."""
        self.mock_repo.get_total_revenue.return_value = 0.0
        self.mock_repo.get_total_orders.return_value = 0
        self.mock_repo.get_total_customers.return_value = 0
        self.mock_repo.get_total_products.return_value = 0
        self.mock_repo.get_average_order_value.return_value = 0.0
        self.mock_repo.get_total_units_sold.return_value = 0
        self.mock_repo.get_cancellation_count.return_value = 0
        self.mock_repo.get_cancellation_rate.return_value = 0.0
        self.mock_repo.get_cancellation_revenue_impact.return_value = 0.0
        self.mock_repo.get_revenue_by_month.return_value = pd.DataFrame()
        self.mock_repo.get_customer_segments.return_value = pd.DataFrame()

        kpis = self.kpi_engine.calculate_all_kpis()

        self.assertIn("total_revenue", kpis)
        self.assertEqual(kpis["total_revenue"].formatted_value, "£0.00")
        self.assertEqual(kpis["total_orders"].value, 0)
        self.assertEqual(kpis["cancellation_rate"].value, 0.0)

    def test_calculate_all_kpis_with_data(self):
        """Verify metric composition with populated mock repository data."""
        self.mock_repo.get_total_revenue.return_value = 1250000.00
        self.mock_repo.get_total_orders.return_value = 12450
        self.mock_repo.get_total_customers.return_value = 8932
        self.mock_repo.get_total_products.return_value = 3500
        self.mock_repo.get_average_order_value.return_value = 100.40
        self.mock_repo.get_total_units_sold.return_value = 145320
        self.mock_repo.get_cancellation_count.return_value = 585
        self.mock_repo.get_cancellation_rate.return_value = 4.7
        self.mock_repo.get_cancellation_revenue_impact.return_value = 58500.00

        # Mock monthly growth trend DataFrame
        monthly_df = pd.DataFrame([
            {"invoice_year": 2010, "invoice_month": 11, "total_revenue": 100000.0, "total_orders": 1000},
            {"invoice_year": 2010, "invoice_month": 12, "total_revenue": 110000.0, "total_orders": 1100},
        ])
        self.mock_repo.get_revenue_by_month.return_value = monthly_df

        cust_df = pd.DataFrame([
            {"customer_type": "Registered", "customer_count": 5000, "total_revenue": 900000.0},
            {"customer_type": "Guest", "customer_count": 3932, "total_revenue": 350000.0},
        ])
        self.mock_repo.get_customer_segments.return_value = cust_df

        kpis = self.kpi_engine.calculate_all_kpis()

        self.assertEqual(kpis["total_revenue"].formatted_value, "£1.25M")
        self.assertEqual(kpis["total_orders"].formatted_value, "12,450")
        self.assertEqual(kpis["revenue_growth_pct"].value, 10.0)  # (110k - 100k)/100k = 10%
        self.assertEqual(kpis["cancellation_rate"].formatted_value, "4.7%")


if __name__ == "__main__":
    unittest.main()
