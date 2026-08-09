"""
products.py
-----------
Product Analytics page view for RetailLens dashboard.
Identifies top revenue-generating and high-volume products with interactive limit controls.
"""

from typing import Any, Dict

import streamlit as st

from analytics.sql_analytics import SQLAnalyticsService
from app.components.charts import plot_top_products
from app.components.tables import render_data_table


def render_products_page(analytics_service: SQLAnalyticsService, filters: Dict[str, Any]) -> None:
    """Renders Product Analytics Page."""
    st.markdown("# 📦 Product Performance Analytics")
    st.markdown("Analyze inventory performance, top revenue generators, and order volume per item.")
    st.markdown("---")

    col_ctrl1, col_ctrl2 = st.columns(2)

    with col_ctrl1:
        limit = st.selectbox(
            "Display Limit:",
            options=[5, 10, 20, 50],
            index=1,
        )

    with col_ctrl2:
        ranking_metric = st.radio(
            "Rank Products By:",
            options=["Revenue (£)", "Units Sold"],
            index=0,
            horizontal=True,
        )

    metric_col = "total_revenue" if ranking_metric == "Revenue (£)" else "total_units_sold"

    if ranking_metric == "Revenue (£)":
        prod_df = analytics_service.get_top_products_by_revenue(limit=limit, country=filters.get("country"))
    else:
        prod_df = analytics_service.get_top_products_by_quantity(limit=limit, country=filters.get("country"))

    # 1. Plotly Horizontal Bar Chart
    st.plotly_chart(plot_top_products(prod_df, metric=metric_col, limit=limit), use_container_width=True)

    st.markdown("---")

    # 2. Product Table Breakdown
    st.markdown(f"### 📋 Product Leaderboard (Top {limit})")
    render_data_table(prod_df)
