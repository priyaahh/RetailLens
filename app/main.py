"""
main.py
-------
Main Streamlit web application entry point for RetailLens.
Configures wide layout, sidebar filter routing, service caching, and error state handling.
"""

import logging
import sys
from pathlib import Path
import streamlit as st

# Add project root directory to python path for clean imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analytics.service import AnalyticsService
from app.components.filters import render_sidebar_filters
from app.pages.customers import render_customers_page
from app.pages.insights import render_insights_page
from app.pages.operations import render_operations_page
from app.pages.overview import render_overview_page
from app.pages.products import render_products_page
from app.pages.sales import render_sales_page

# Configure page metadata and wide layout
st.set_page_config(
    page_title="RetailLens Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def init_analytics_service():
    """Initializes and caches the master AnalyticsService application layer."""
    return AnalyticsService()


@st.cache_data(ttl=300)
def fetch_country_list(_analytics_service: AnalyticsService):
    """Fetches and caches country filter choices for 5 minutes."""
    return _analytics_service.get_available_countries()


def main():
    """Main application execution router."""
    try:
        # Initialize Cached Analytics Service
        analytics_service = init_analytics_service()

        # Fetch Countries for Filter Menu
        countries = fetch_country_list(analytics_service)

        # Render Sidebar Navigation & Filters
        filters = render_sidebar_filters(countries)

        # Page Router
        page = filters.get("page", "Executive Overview")

        if page == "Executive Overview":
            render_overview_page(analytics_service.kpi_engine, analytics_service.repository, filters)
        elif page == "Sales Analytics":
            render_sales_page(analytics_service.repository, filters)
        elif page == "Product Analytics":
            render_products_page(analytics_service.repository, filters)
        elif page == "Customer Analytics":
            render_customers_page(analytics_service.repository, filters)
        elif page == "Business Insights":
            render_insights_page(analytics_service, filters)
        elif page == "Operations Analytics":
            render_operations_page(analytics_service.kpi_engine, analytics_service.repository, filters)

    except Exception as e:
        st.error("⚠️ Unable to connect to the analytics database. Please check configuration or try again later.")
        st.info("Ensure environment variables are configured correctly in your .env file.")
        logging.error("Streamlit Main Application Error: %s", str(e), exc_info=True)


if __name__ == "__main__":
    main()
