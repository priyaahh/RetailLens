"""
filters.py
----------
Reusable sidebar filters component for RetailLens Streamlit dashboard.
Collects user filter inputs and triggers cache clear events.
"""

from typing import Any, Dict, List

import streamlit as st


def render_sidebar_filters(available_countries: List[str]) -> Dict[str, Any]:
    """
    Renders sidebar filters and navigation menu.

    :param available_countries: List of country strings available in the database.
    :return: Dictionary containing user-selected filter parameters.
    """
    st.sidebar.markdown("## 📊 RetailLens Navigation")

    page = st.sidebar.radio(
        "Select Module View",
        options=[
            "Executive Overview",
            "Sales Analytics",
            "Product Analytics",
            "Customer Analytics",
            "Business Insights",
            "Operations Analytics",
            "Pipeline Monitor",
        ],
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎛️ Interactive Filters")

    # 1. Date Range Filter
    col_start, col_end = st.sidebar.columns(2)
    start_date = col_start.date_input("Start Date", value=None)
    end_date = col_end.date_input("End Date", value=None)

    start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
    end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

    # 2. Country Filter
    selected_country = st.sidebar.selectbox(
        "Country Market",
        options=available_countries if available_countries else ["All Countries"],
        index=0,
    )

    # 3. Customer Type Filter
    selected_customer_type = st.sidebar.selectbox(
        "Customer Account Type",
        options=["All", "Registered", "Guest"],
        index=0,
    )

    # 4. Transaction Type Filter
    selected_transaction_type = st.sidebar.selectbox(
        "Transaction Status",
        options=["All", "Sales", "Cancellations"],
        index=0,
    )

    st.sidebar.markdown("---")

    # Refresh Data Cache Button
    if st.sidebar.button("🔄 Refresh Data Cache"):
        st.cache_data.clear()
        st.sidebar.success("Database query cache cleared!")

    return {
        "page": page,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "country": selected_country,
        "customer_type": selected_customer_type,
        "transaction_type": selected_transaction_type,
    }
