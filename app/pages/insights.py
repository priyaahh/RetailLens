"""
insights.py
-----------
Automated Business Insights page view for RetailLens dashboard.
Renders automated observations, severity alerts, and actionable recommendations.
"""

from typing import Any, Dict

import streamlit as st

from analytics.models import FilterParams
from analytics.service import AnalyticsService
from app.components.insights_cards import render_insights_cards


def render_insights_page(analytics_service: AnalyticsService, filters: Dict[str, Any]) -> None:
    """Renders Automated Business Insights Page."""
    st.markdown("# 💡 Automated Business Insights & Recommendations")
    st.markdown("Automated anomaly detection, operational risk identification, and strategic recommendations.")
    st.markdown("---")

    filter_obj = FilterParams(
        start_date=filters.get("start_date"),
        end_date=filters.get("end_date"),
        country=filters.get("country"),
        customer_type=filters.get("customer_type"),
        transaction_type=filters.get("transaction_type"),
    )

    try:
        insights = analytics_service.get_business_insights(filter_obj)
        render_insights_cards(insights)
    except Exception as e:
        st.error(f"⚠️ Unable to generate automated business insights: {str(e)}")
