"""
kpi_engine.py
--------------
Business KPI Calculation Engine for RetailLens.
Composes data access results from AnalyticsRepository into structured, typed KPIMetric objects
with formatted values, business definitions, and zero/null protection.
"""

import logging
from typing import Dict, Optional, Union

import pandas as pd

from analytics.models import FilterParams, KPIMetric
from analytics.repository import AnalyticsRepository
from app.utils.formatting import format_currency, format_number, format_percentage

logger = logging.getLogger(__name__)


class KPIEngine:
    """Business KPI Metric Calculation Engine."""

    def __init__(self, repository: Optional[AnalyticsRepository] = None):
        """Dependency injection constructor for AnalyticsRepository."""
        self.repository = repository or AnalyticsRepository()

    def calculate_all_kpis(self, filters: Optional[FilterParams] = None) -> Dict[str, KPIMetric]:
        """Calculates and returns all Core, Sales, Customer, and Cancellation business KPIs."""
        kpis: Dict[str, KPIMetric] = {}

        # ---------------------------------------------------------------------
        # 1. CORE KPIs
        # ---------------------------------------------------------------------
        total_rev = self.repository.get_total_revenue(filters)
        kpis["total_revenue"] = KPIMetric(
            name="Total Net Revenue",
            value=total_rev,
            formatted_value=format_currency(total_rev),
            category="CORE",
            description="Total net monetary revenue generated across all completed sales.",
            unit="£",
        )

        total_ord = self.repository.get_total_orders(filters)
        kpis["total_orders"] = KPIMetric(
            name="Total Completed Orders",
            value=total_ord,
            formatted_value=format_number(total_ord),
            category="CORE",
            description="Count of distinct completed sales invoices.",
            unit="orders",
        )

        total_cust = self.repository.get_total_customers(filters)
        kpis["total_customers"] = KPIMetric(
            name="Total Distinct Customers",
            value=total_cust,
            formatted_value=format_number(total_cust),
            category="CORE",
            description="Count of distinct buyers (including guest checkout marker).",
            unit="customers",
        )

        total_prod = self.repository.get_total_products(filters)
        kpis["total_products"] = KPIMetric(
            name="Catalog Product Count",
            value=total_prod,
            formatted_value=format_number(total_prod),
            category="CORE",
            description="Total unique items/stock codes sold.",
            unit="items",
        )

        aov = self.repository.get_average_order_value(filters)
        kpis["average_order_value"] = KPIMetric(
            name="Average Order Value (AOV)",
            value=aov,
            formatted_value=format_currency(aov),
            category="CORE",
            description="Average monetary spend per completed invoice order.",
            unit="£",
        )

        units_sold = self.repository.get_total_units_sold(filters)
        items_per_order = round(units_sold / total_ord, 1) if total_ord > 0 else 0.0
        kpis["average_items_per_order"] = KPIMetric(
            name="Average Items per Order",
            value=items_per_order,
            formatted_value=f"{items_per_order:.1f}",
            category="CORE",
            description="Average physical item volume purchased per completed invoice.",
            unit="items",
        )

        # ---------------------------------------------------------------------
        # 2. CANCELLATION KPIs
        # ---------------------------------------------------------------------
        cancel_cnt = self.repository.get_cancellation_count(filters)
        kpis["cancellation_count"] = KPIMetric(
            name="Cancelled Order Count",
            value=cancel_cnt,
            formatted_value=format_number(cancel_cnt),
            category="CANCELLATION",
            description="Total number of returned or cancelled order invoices.",
            unit="invoices",
        )

        cancel_rate = self.repository.get_cancellation_rate(filters)
        kpis["cancellation_rate"] = KPIMetric(
            name="Cancellation Rate",
            value=cancel_rate,
            formatted_value=format_percentage(cancel_rate),
            category="CANCELLATION",
            description="Percentage of generated invoices representing returns or cancellations.",
            unit="%",
        )

        cancel_impact = self.repository.get_cancellation_revenue_impact(filters)
        kpis["cancellation_revenue_impact"] = KPIMetric(
            name="Cancellation Revenue Loss",
            value=cancel_impact,
            formatted_value=format_currency(cancel_impact),
            category="CANCELLATION",
            description="Total monetary revenue lost due to returns and order cancellations.",
            unit="£",
        )

        # ---------------------------------------------------------------------
        # 3. SALES & GROWTH KPIs
        # ---------------------------------------------------------------------
        monthly_df = self.repository.get_revenue_by_month(filters)
        rev_growth_pct = 0.0
        order_growth_pct = 0.0

        if not monthly_df.empty and len(monthly_df) >= 2:
            curr_rev = float(monthly_df.iloc[-1]["total_revenue"])
            prev_rev = float(monthly_df.iloc[-2]["total_revenue"])
            if prev_rev > 0:
                rev_growth_pct = round(((curr_rev - prev_rev) / prev_rev) * 100, 2)

            curr_ord = float(monthly_df.iloc[-1]["total_orders"])
            prev_ord = float(monthly_df.iloc[-2]["total_orders"])
            if prev_ord > 0:
                order_growth_pct = round(((curr_ord - prev_ord) / prev_ord) * 100, 2)

        kpis["revenue_growth_pct"] = KPIMetric(
            name="Month-over-Month Revenue Growth",
            value=rev_growth_pct,
            formatted_value=format_percentage(rev_growth_pct),
            category="SALES",
            description="Percentage revenue change compared to previous month.",
            unit="%",
        )

        kpis["monthly_order_growth_pct"] = KPIMetric(
            name="Month-over-Month Order Growth",
            value=order_growth_pct,
            formatted_value=format_percentage(order_growth_pct),
            category="SALES",
            description="Percentage order volume change compared to previous month.",
            unit="%",
        )

        # ---------------------------------------------------------------------
        # 4. CUSTOMER KPIs
        # ---------------------------------------------------------------------
        cust_df = self.repository.get_customer_segments(filters)
        reg_cnt = 0
        guest_cnt = 0
        reg_rev = 0.0

        if not cust_df.empty:
            for _, row in cust_df.iterrows():
                ctype = str(row["customer_type"])
                if ctype == "Registered":
                    reg_cnt = int(row["customer_count"])
                    reg_rev = float(row["total_revenue"])
                elif ctype == "Guest":
                    guest_cnt = int(row["customer_count"])

        kpis["registered_customers"] = KPIMetric(
            name="Registered Customer Accounts",
            value=reg_cnt,
            formatted_value=format_number(reg_cnt),
            category="CUSTOMER",
            description="Number of distinct registered buyer accounts.",
            unit="accounts",
        )

        kpis["guest_customers"] = KPIMetric(
            name="Guest Checkouts",
            value=guest_cnt,
            formatted_value=format_number(guest_cnt),
            category="CUSTOMER",
            description="Number of unauthenticated guest checkout orders.",
            unit="orders",
        )

        kpis["registered_customer_revenue"] = KPIMetric(
            name="Registered Account Revenue",
            value=reg_rev,
            formatted_value=format_currency(reg_rev),
            category="CUSTOMER",
            description="Monetary sales revenue generated by registered accounts.",
            unit="£",
        )

        rev_per_cust = round(total_rev / total_cust, 2) if total_cust > 0 else 0.0
        kpis["revenue_per_customer"] = KPIMetric(
            name="Average Revenue per Customer",
            value=rev_per_cust,
            formatted_value=format_currency(rev_per_cust),
            category="CUSTOMER",
            description="Average sales revenue generated per customer.",
            unit="£",
        )

        return kpis
