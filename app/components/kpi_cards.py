"""
kpi_cards.py
------------
Reusable KPI card metrics grid component for Streamlit dashboard.
"""

from typing import Dict, Union

import streamlit as st

from app.utils.formatting import format_currency, format_number, format_percentage


def render_kpi_cards(kpi_data: Dict[str, Union[float, int, str]]) -> None:
    """
    Renders a responsive 6-card metric grid for executive dashboard KPIs.

    :param kpi_data: Dictionary of calculated KPI values.
    """
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            label="Total Revenue",
            value=format_currency(kpi_data.get("total_revenue", 0.0)),
        )

    with col2:
        st.metric(
            label="Total Orders",
            value=format_number(kpi_data.get("total_orders", 0)),
        )

    with col3:
        st.metric(
            label="Total Customers",
            value=format_number(kpi_data.get("total_customers", 0)),
        )

    with col4:
        st.metric(
            label="Average Order Value",
            value=format_currency(kpi_data.get("average_order_value", 0.0)),
        )

    with col5:
        st.metric(
            label="Total Units Sold",
            value=format_number(kpi_data.get("total_units_sold", 0)),
        )

    with col6:
        st.metric(
            label="Cancellation Rate",
            value=format_percentage(kpi_data.get("cancellation_rate_pct", 0.0)),
        )
