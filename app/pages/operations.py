"""
operations.py
-------------
Operations & Cancellation Analytics page view for RetailLens dashboard.
Monitors order returns, cancellation volume, lost revenue trends, and problematic products.
"""

from typing import Any, Dict

import streamlit as st

from analytics.kpis import KPICalculator
from analytics.sql_analytics import SQLAnalyticsService
from app.components.charts import plot_cancellation_trend
from app.components.tables import render_data_table
from app.utils.formatting import format_currency, format_percentage


def render_operations_page(
    kpi_calc: KPICalculator, analytics_service: SQLAnalyticsService, filters: Dict[str, Any]
) -> None:
    """Renders Operations & Cancellation Analytics Page."""
    st.markdown("# ⚠️ Operations & Cancellation Analytics")
    st.markdown("Monitor order cancellations, returns, monetary revenue loss, and item return frequencies.")
    st.markdown("---")

    # 1. Operations KPI Cards
    try:
        cancel_rate = kpi_calc.cancellation_rate(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            country=filters.get("country"),
        )
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cancellation Rate", format_percentage(cancel_rate))
        with col2:
            st.warning("⚠️ Cancellations are tracked separately from gross completed sales.")
    except Exception as e:
        st.error(f"Unable to calculate cancellation metrics: {str(e)}")

    st.markdown("---")

    # 2. Lost Revenue Cancellation Trend
    st.markdown("### 📉 Monthly Lost Revenue Trend")
    cancel_trend_df = analytics_service.get_cancellation_trend(
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
    )
    st.plotly_chart(plot_cancellation_trend(cancel_trend_df), use_container_width=True)

    st.markdown("---")

    # 3. Top Returned/Cancelled Products Table
    st.markdown("### 📦 Top Returned / Cancelled Products")
    cancel_prod_df = analytics_service.get_products_by_cancellation(
        limit=10, country=filters.get("country")
    )
    render_data_table(cancel_prod_df)
