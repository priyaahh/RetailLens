# 💻 Dashboard Architecture & User Experience Notes

This document details the frontend Streamlit architecture, caching mechanisms, UI components, and state routing of **RetailLens**.

---

## 🏛️ 1. Multi-Page Architecture & View Separation

The dashboard is split across 6 dedicated views inside `app/pages/`:

1. **Executive Overview (`overview.py`)**: Top KPI cards, monthly revenue line chart, top geographic markets, and customer revenue breakdown.
2. **Sales Analytics (`sales.py`)**: Granular time-series trends (Daily/Weekly/Monthly/Quarterly), order volume, AOV, and market tables.
3. **Product Analytics (`products.py`)**: Inventory rankings with Top 5/10/20/50 controls by Revenue or Quantity.
4. **Customer Analytics (`customers.py`)**: Registered vs Guest buyer share and spending leaderboards.
5. **Business Insights (`insights.py`)**: Automated observations, severity alerts, and actionable recommendations.
6. **Operations Analytics (`operations.py`)**: Monitors cancellation rates, return frequencies, lost revenue trends, and problematic items.

---

## ⚡ 2. Two-Tier Streamlit Caching

* **Tier 1 (`@st.cache_resource`)**: Caches persistent service objects (`AnalyticsService`) and SQLAlchemy connection pools globally across all user sessions.
* **Tier 2 (`@st.cache_data(ttl=300)`)**: Caches read-only query DataFrames and country lists for 5 minutes (300 seconds), delivering sub-second page switches.
* **Manual Cache Invalidation**: The sidebar includes a `"🔄 Refresh Data Cache"` button executing `st.cache_data.clear()`.
