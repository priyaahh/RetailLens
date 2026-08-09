"""
sales.py
--------
Sales & Revenue Analytics page view for RetailLens dashboard.
Provides granular trend exploration (Daily/Weekly/Monthly/Quarterly), order volume, AOV, and market breakdown.
"""

from typing import Any, Dict

import plotly.express as px
import streamlit as st

from analytics.sql_analytics import SQLAnalyticsService
from app.components.charts import plot_revenue_by_country, plot_revenue_trend
from app.components.tables import render_data_table


def render_sales_page(analytics_service: SQLAnalyticsService, filters: Dict[str, Any]) -> None:
    """Renders Sales Analytics Page."""
    st.markdown("# 💰 Revenue & Sales Analytics")
    st.markdown("Detailed breakdown of sales performance across time granularities and geographic markets.")
    st.markdown("---")

    # Granularity Radio Selector
    granularity = st.radio(
        "Select Time Granularity:",
        options=["Daily", "Weekly", "Monthly", "Quarterly"],
        index=2,
        horizontal=True,
    )

    trend_df = analytics_service.get_revenue_trend(
        granularity=granularity,
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        country=filters.get("country"),
    )

    # 1. Main Revenue Line Chart
    st.plotly_chart(plot_revenue_trend(trend_df, granularity), use_container_width=True)

    st.markdown("---")

    # 2. Order Volume & AOV Trends
    col_vol, col_aov = st.columns(2)

    with col_vol:
        st.markdown("### 📦 Order Volume Trend")
        if not trend_df.empty and "period" in trend_df.columns:
            fig_vol = px.line(
                trend_df,
                x="period",
                y="total_orders",
                title=f"Order Volume ({granularity})",
                markers=True,
            )
            fig_vol.update_traces(line_color="#2E7D32")
            fig_vol.update_layout(template="plotly_white")
            st.plotly_chart(fig_vol, use_container_width=True)
        else:
            st.info("No volume data available.")

    with col_aov:
        st.markdown("### 💳 Average Order Value Trend (£)")
        if not trend_df.empty and "period" in trend_df.columns:
            fig_aov = px.line(
                trend_df,
                x="period",
                y="average_order_value",
                title=f"AOV Trajectory (£)",
                markers=True,
            )
            fig_aov.update_traces(line_color="#7B1FA2")
            fig_aov.update_layout(template="plotly_white")
            st.plotly_chart(fig_aov, use_container_width=True)
        else:
            st.info("No AOV data available.")

    st.markdown("---")

    # 3. Country Performance Table
    st.markdown("### 🌍 Geographic Performance Breakdown")
    geo_df = analytics_service.get_revenue_by_country()
    render_data_table(geo_df)
