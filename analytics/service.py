"""
service.py
----------
Analytics Application Service Layer for RetailLens.
Composes data access results from AnalyticsRepository, metric compositions from KPIEngine,
and business observations from InsightEngine into clean, high-level API methods for Streamlit UI views.
Decouples UI code completely from database connection and SQL execution logic.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from analytics.exceptions import AnalyticsError, InvalidFilterError, RepositoryError
from analytics.insights import InsightEngine
from analytics.kpi_engine import KPIEngine
from analytics.models import DashboardSummary, FilterParams, Insight, KPIMetric
from analytics.repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Application Service Layer composing analytics repositories, KPI engines, and insight engines."""

    def __init__(
        self,
        repository: Optional[AnalyticsRepository] = None,
        kpi_engine: Optional[KPIEngine] = None,
        insight_engine: Optional[InsightEngine] = None,
    ):
        """Dependency injection constructor for repository, KPI engine, and insight engine."""
        self.repository = repository or AnalyticsRepository()
        self.kpi_engine = kpi_engine or KPIEngine(repository=self.repository)
        self.insight_engine = insight_engine or InsightEngine(repository=self.repository)

    def get_dashboard_summary(self, filters: Optional[FilterParams] = None) -> DashboardSummary:
        """
        Orchestrates and returns a complete DashboardSummary package for the Streamlit Overview page.

        :param filters: Optional FilterParams instance.
        :return: Composed DashboardSummary dataclass.
        """
        logger.info("Orchestrating executive dashboard summary package...")
        try:
            kpis = self.kpi_engine.calculate_all_kpis(filters)
            insights = self.insight_engine.generate_insights(kpis, filters)
            trend_df = self.repository.get_revenue_by_month(filters)
            top_products_df = self.repository.get_top_products(filters, limit=5)
            country_df = self.repository.get_revenue_by_country(filters, limit=10)
            cust_summary_df = self.repository.get_customer_segments(filters)

            return DashboardSummary(
                kpis=kpis,
                insights=insights,
                revenue_trend=trend_df,
                top_products=top_products_df,
                country_revenue=country_df,
                customer_summary=cust_summary_df,
            )
        except Exception as e:
            logger.error("Failed to generate dashboard summary: %s", str(e), exc_info=True)
            raise AnalyticsError(f"Analytics service failed to compose dashboard summary: {str(e)}")

    def get_sales_trends(self, filters: Optional[FilterParams] = None) -> pd.DataFrame:
        """Retrieves sales and revenue trends."""
        return self.repository.get_revenue_by_month(filters)

    def get_customer_analysis(self, filters: Optional[FilterParams] = None) -> Dict[str, Any]:
        """Retrieves customer segment breakdown and top spenders leaderboard."""
        summary_df = self.repository.get_customer_segments(filters)
        return {"summary": summary_df}

    def get_product_analysis(
        self, filters: Optional[FilterParams] = None, limit: int = 10, metric: str = "total_revenue"
    ) -> pd.DataFrame:
        """Retrieves product performance leaderboard."""
        return self.repository.get_top_products(filters, limit=limit, metric=metric)

    def get_country_analysis(
        self, filters: Optional[FilterParams] = None, limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Retrieves geographic country revenue breakdown."""
        return self.repository.get_revenue_by_country(filters, limit=limit)

    def get_cancellation_analysis(self, filters: Optional[FilterParams] = None) -> Dict[str, Any]:
        """Retrieves cancellation metrics and top returned items."""
        kpis = self.kpi_engine.calculate_all_kpis(filters)
        top_returned_df = self.repository.get_top_products(filters, limit=10, metric="total_units_sold")
        return {
            "cancellation_rate": kpis.get("cancellation_rate"),
            "cancellation_loss": kpis.get("cancellation_revenue_impact"),
            "cancellation_count": kpis.get("cancellation_count"),
            "top_returned_products": top_returned_df,
        }

    def get_business_insights(self, filters: Optional[FilterParams] = None) -> List[Insight]:
        """Generates automated business insight objects."""
        kpis = self.kpi_engine.calculate_all_kpis(filters)
        return self.insight_engine.generate_insights(kpis, filters)

    def get_available_countries(self) -> List[str]:
        """Retrieves distinct country dropdown choices."""
        return self.repository.get_available_countries()
