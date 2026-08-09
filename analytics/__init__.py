"""
RetailLens Analytics Engine package initialization.
Exposes public API services, repositories, engines, and domain models.
"""

from analytics.exceptions import (
    AnalyticsError,
    DatabaseConnectionError,
    InvalidFilterError,
    RepositoryError,
)
from analytics.insights import InsightEngine
from analytics.kpi_engine import KPIEngine
from analytics.models import DashboardSummary, FilterParams, Insight, KPIMetric
from analytics.repository import AnalyticsRepository
from analytics.service import AnalyticsService

__all__ = [
    "AnalyticsService",
    "AnalyticsRepository",
    "KPIEngine",
    "InsightEngine",
    "FilterParams",
    "Insight",
    "KPIMetric",
    "DashboardSummary",
    "AnalyticsError",
    "RepositoryError",
    "DatabaseConnectionError",
    "InvalidFilterError",
]
