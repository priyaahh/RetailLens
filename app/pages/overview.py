"""
overview.py
-----------
Executive Overview page view for RetailLens dashboard.
Displays high-level KPI cards, top-level sales trajectory, geography, and customer mix.
"""

from typing import Any, Dict

import streamlit as st

from analytics.kpis import KPICalculator
from analytics.sql_analytics import SQLAnalyticsService
from app.components.charts import (
    plot_customer_distribution,
    plot_revenue_by_country,
    plot_revenue_trend,
)
from app.components.kpi_cards import render_kpi_cards
from app.components.tables import render_data_table


def render_overview_page(
    kpi_calc: KPICalculator, analytics_service: SQLAnalyticsService, filters: Dict[str, Any]
) -> None:
    """
    Renders Executive Overview page.

    :param kpi_calc: Instantiated KPICalculator instance.
    :param analytics_service: Instantiated SQLAnalyticsService instance.
    :param filters: Filter parameters dict.
    """
    st.markdown("# 📊 Executive Overview")
    st.markdown("Real-time executive health metrics, sales trajectory, and geographic market breakdown.")
    st.markdown("---")

    # 1. KPI Cards Grid
    try:
        kpi_data = kpi_calc.get_filtered_kpis(
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            country=filters.get("country"),
            customer_type=filters.get("customer_type"),
        )
        render_kpi_cards(kpi_data)
    except Exception as e:
        st.error(f"⚠️ Unable to load KPI metrics from database: {str(e)}")

    st.markdown("---")

    # 2. Revenue Trend & Geographic Charts
    col_trend, col_geo = st.columns([3, 2])

    with col_trend:
        st.markdown("### 📈 Revenue Trajectory")
        trend_df = analytics_service.get_revenue_trend(
            granularity="Monthly",
            start_date=filters.get("start_date"),
            end_date=filters.get("end_date"),
            country=filters.get("country"),
        )
        st.plotly_chart(plot_revenue_trend(trend_df, "Monthly"), use_container_width=True)

    with col_geo:
        st.markdown("### 🌍 Top Markets")
        geo_df = analytics_service.get_revenue_by_country(limit=10)
        st.plotly_chart(plot_revenue_by_country(geo_df, limit=10), use_container_width=True)

    st.markdown("---")

    # 3. Customer Breakdown & Top Products Quick Summary
    col_cust, col_prod = st.columns([2, 3])

    with col_cust:
        st.markdown("### 👥 Customer Mix")
        cust_df = analytics_service.get_customer_summary(country=filters.get("country"))
        st.plotly_chart(plot_customer_distribution(cust_df), use_container_width=True)

    with col_prod:
        st.markdown("### 📦 Top 5 Products Summary")
        prod_df = analytics_service.get_top_products_by_revenue(limit=5, country=filters.get("country"))
        render_data_table(prod_df)
