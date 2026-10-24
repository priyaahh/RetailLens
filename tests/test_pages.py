"""
test_pages.py
-------------
Automated unit tests verifying that all 7 Streamlit dashboard pages render
cleanly without errors against an empty database.
Guarantees compatibility across SQLAnalyticsService, KPICalculator,
AnalyticsService, and AnalyticsRepository.
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine

from analytics.kpis import KPICalculator
from analytics.pipeline_repository import PipelineMonitoringRepository
from analytics.pipeline_service import PipelineMonitoringService
from analytics.repository import AnalyticsRepository
from analytics.service import AnalyticsService
from analytics.sql_analytics import SQLAnalyticsService
from app.pages.customers import render_customers_page
from app.pages.insights import render_insights_page
from app.pages.operations import render_operations_page
from app.pages.overview import render_overview_page
from app.pages.pipeline_monitor import render_pipeline_monitor_page
from app.pages.products import render_products_page
from app.pages.sales import render_sales_page
from database.init_db import initialize_database


class TestDashboardPages(unittest.TestCase):
    """Test suite ensuring all dashboard pages render without errors on an empty database."""

    @classmethod
    def setUpClass(cls):
        """Creates a temporary SQLite database and initializes the full schema."""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = cls.temp_db.name
        cls.temp_db.close()

        cls.db_url = f"sqlite:///{cls.db_path}"
        os.environ["DATABASE_URL"] = cls.db_url
        os.environ["APP_ENV"] = "testing"

        from config.app_config import get_config
        get_config(reload=True)

        # Initialize schema tables
        initialize_database()

        cls.engine = create_engine(cls.db_url, connect_args={"check_same_thread": False})
        cls.kpi_calc = KPICalculator(engine=cls.engine)
        cls.sql_service = SQLAnalyticsService(engine=cls.engine)
        cls.repo = AnalyticsRepository(engine=cls.engine)
        cls.analytics_service = AnalyticsService(repository=cls.repo)
        cls.pipe_repo = PipelineMonitoringRepository(engine=cls.engine)
        cls.monitoring_service = PipelineMonitoringService(repository=cls.pipe_repo)

        cls.default_filters = {
            "start_date": None,
            "end_date": None,
            "country": "All Countries",
            "customer_type": "All",
            "transaction_type": "All",
        }

    @classmethod
    def tearDownClass(cls):
        """Cleans up the temporary SQLite database file."""
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except Exception:
                pass

    def test_render_overview_page(self):
        """Verify Executive Overview page renders without error on empty DB."""
        try:
            render_overview_page(self.kpi_calc, self.sql_service, self.default_filters)
        except Exception as e:
            self.fail(f"render_overview_page raised an unexpected exception: {e}")

    def test_render_sales_page(self):
        """Verify Sales Analytics page renders without error on empty DB."""
        try:
            render_sales_page(self.sql_service, self.default_filters)
        except Exception as e:
            self.fail(f"render_sales_page raised an unexpected exception: {e}")

    def test_render_products_page(self):
        """Verify Product Analytics page renders without error on empty DB."""
        try:
            render_products_page(self.sql_service, self.default_filters)
        except Exception as e:
            self.fail(f"render_products_page raised an unexpected exception: {e}")

    def test_render_customers_page(self):
        """Verify Customer Analytics page renders without error on empty DB."""
        try:
            render_customers_page(self.sql_service, self.default_filters)
        except Exception as e:
            self.fail(f"render_customers_page raised an unexpected exception: {e}")

    def test_render_insights_page(self):
        """Verify Business Insights page renders without error on empty DB."""
        try:
            render_insights_page(self.analytics_service, self.default_filters)
        except Exception as e:
            self.fail(f"render_insights_page raised an unexpected exception: {e}")

    def test_render_operations_page(self):
        """Verify Operations Analytics page renders without error on empty DB."""
        try:
            render_operations_page(self.kpi_calc, self.sql_service, self.default_filters)
        except Exception as e:
            self.fail(f"render_operations_page raised an unexpected exception: {e}")

    def test_render_pipeline_monitor_page(self):
        """Verify Pipeline Monitor page renders without error on empty DB."""
        try:
            render_pipeline_monitor_page(self.monitoring_service)
        except Exception as e:
            self.fail(f"render_pipeline_monitor_page raised an unexpected exception: {e}")

    def test_repository_compatibility_bridge(self):
        """Verify AnalyticsRepository provides get_revenue_trend and other page methods without AttributeError."""
        self.assertTrue(hasattr(self.repo, "get_revenue_trend"))
        trend_df = self.repo.get_revenue_trend(granularity="Monthly")
        self.assertIsNotNone(trend_df)

        self.assertTrue(hasattr(self.repo, "get_customer_summary"))
        cust_df = self.repo.get_customer_summary()
        self.assertIsNotNone(cust_df)

        self.assertTrue(hasattr(self.repo, "get_top_products_by_revenue"))
        prod_df = self.repo.get_top_products_by_revenue(limit=5)
        self.assertIsNotNone(prod_df)

        self.assertTrue(hasattr(self.repo, "get_top_products_by_quantity"))
        prod_qty_df = self.repo.get_top_products_by_quantity(limit=5)
        self.assertIsNotNone(prod_qty_df)

        self.assertTrue(hasattr(self.repo, "get_top_customers_by_revenue"))
        top_cust_df = self.repo.get_top_customers_by_revenue(limit=5)
        self.assertIsNotNone(top_cust_df)

        self.assertTrue(hasattr(self.repo, "get_cancellation_trend"))
        cancel_trend_df = self.repo.get_cancellation_trend()
        self.assertIsNotNone(cancel_trend_df)

        self.assertTrue(hasattr(self.repo, "get_products_by_cancellation"))
        cancel_prods_df = self.repo.get_products_by_cancellation(limit=5)
        self.assertIsNotNone(cancel_prods_df)

    def test_pages_rendered_with_repository_bridge(self):
        """Verify pages still render without error even if AnalyticsRepository is passed."""
        try:
            # Test that overview and sales do NOT crash with AttributeError when repo is passed
            render_overview_page(self.analytics_service.kpi_engine, self.repo, self.default_filters)
            render_sales_page(self.repo, self.default_filters)
            render_products_page(self.repo, self.default_filters)
            render_customers_page(self.repo, self.default_filters)
            render_operations_page(self.analytics_service.kpi_engine, self.repo, self.default_filters)
        except Exception as e:
            self.fail(f"Passing repository to pages raised an unexpected exception: {e}")


if __name__ == "__main__":
    unittest.main()
