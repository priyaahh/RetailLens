"""
insights_cards.py
------------------
UI component rendering automated Business Insight objects with severity badges, metrics, and actionable recommendations.
"""

from typing import List

import streamlit as st

from analytics.models import Insight


def render_insights_cards(insights: List[Insight]) -> None:
    """
    Renders structured Business Insight cards with color-coded severity alerts and recommendations.

    :param insights: List of Insight dataclass objects.
    """
    if not insights:
        st.success("✅ Operational Healthy Status: No critical anomalies or high risks detected for selected filters.")
        return

    for insight in insights:
        severity = insight.severity.upper()
        if severity == "CRITICAL":
            icon = "🔴"
            container = st.error
        elif severity == "HIGH":
            icon = "🟠"
            container = st.warning
        elif severity == "MEDIUM":
            icon = "🟡"
            container = st.info
        else:
            icon = "🟢"
            container = st.success

        with container(f"{icon} [{insight.category}] {insight.title}"):
            st.markdown(f"**Description**: {insight.description}")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Observed Metric**: `{insight.metric} = {insight.value}`")
            with col2:
                st.markdown(f"**Configured Threshold**: `{insight.threshold}`")
            st.markdown(f"💡 **Actionable Recommendation**: *{insight.recommendation}*")
