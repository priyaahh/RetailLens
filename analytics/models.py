"""
models.py
---------
Typed domain models and data structures for RetailLens analytics, KPIs, insights, and filters.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from analytics.exceptions import InvalidFilterError


@dataclass
class FilterParams:
    """Encapsulates user-supplied analytics dashboard filter parameters."""

    start_date: Optional[str] = None
    end_date: Optional[str] = None
    country: Optional[str] = None
    customer_type: Optional[str] = None
    transaction_type: Optional[str] = None

    def validate(self) -> None:
        """Validates filter parameter sanity (e.g., date formatting and chronological order)."""
        if self.start_date and self.end_date:
            try:
                dt_start = datetime.strptime(self.start_date, "%Y-%m-%d")
                dt_end = datetime.strptime(self.end_date, "%Y-%m-%d")
                if dt_start > dt_end:
                    raise InvalidFilterError(
                        f"Start date ({self.start_date}) cannot be after end date ({self.end_date})."
                    )
            except ValueError as e:
                if isinstance(e, InvalidFilterError):
                    raise
                raise InvalidFilterError(f"Invalid date format: {str(e)}. Expected YYYY-MM-DD.")


@dataclass
class KPIMetric:
    """Represents a calculated business KPI metric."""

    name: str
    value: Union[float, int, str]
    formatted_value: str
    category: str
    description: str
    unit: str = ""


@dataclass
class Insight:
    """Represents an automated structured business insight observation."""

    category: str  # SALES, CUSTOMER, PRODUCT, CANCELLATION, TREND, ANOMALY
    title: str
    description: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    metric: str
    value: Union[float, int, str]
    threshold: Union[float, int, str]
    recommendation: str


@dataclass
class DashboardSummary:
    """Composed summary package delivered to Streamlit UI layer."""

    kpis: Dict[str, KPIMetric]
    insights: List[Insight]
    revenue_trend: pd.DataFrame
    top_products: pd.DataFrame
    country_revenue: pd.DataFrame
    customer_summary: pd.DataFrame
