"""
customers.py
------------
Customer Analytics page view for RetailLens dashboard.
Displays registered vs guest buyer behavior, customer revenue contribution, and spending leaderboards.
"""

from typing import Any, Dict

import streamlit as st

from analytics.sql_analytics import SQLAnalyticsService
from app.components.charts import plot_customer_distribution
from app.components.tables import render_data_table


def render_customers_page(analytics_service: SQLAnalyticsService, filters: Dict[str, Any]) -> None:
    """Renders Customer Analytics Page."""
    st.markdown("# 👥 Customer Behavior Analytics")
    st.markdown("Explore spending patterns of registered customer accounts versus guest checkouts.")
    st.markdown("---")

    col_chart, col_summary = st.columns([1, 1])

    with col_chart:
        st.markdown("### 🍩 Revenue Share by Customer Type")
        cust_summary_df = analytics_service.get_customer_summary(country=filters.get("country"))
        st.plotly_chart(plot_customer_distribution(cust_summary_df), use_container_width=True)

    with col_summary:
        st.markdown("### 📋 Segment Summary")
        render_data_table(cust_summary_df)

    st.markdown("---")

    # Top Customer Leaderboard
    st.markdown("### 🏆 Top Spending Customer Leaderboard")
    top_cust_limit = st.slider("Select Leaderboard Depth:", min_value=5, max_value=50, value=10, step=5)

    top_cust_df = analytics_service.get_top_customers_by_revenue(
        limit=top_cust_limit, country=filters.get("country")
    )
    render_data_table(top_cust_df)
