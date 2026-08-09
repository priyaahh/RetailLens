# ⚡ Phase 4 Dashboard Cheat Sheet (5-Minute Revision Guide)

---

## 📐 Architecture Flow

```text
Streamlit UI (main.py)  ──►  Components (kpi_cards/charts)  ──►  SQLAnalyticsService  ──►  PostgreSQL
```

---

## 🔑 One-Line Definitions

* **Streamlit**: Pure-Python framework for building interactive, reactive web dashboards without writing HTML/CSS/JS.
* **Plotly**: JavaScript-powered visualization engine providing interactive charts with tooltips, panning, and zooming.
* **KPI Card**: Executive metric block (`st.metric`) displaying high-level quantitative indicators.
* **SQL Pushdown**: Passing sidebar filter choices directly into PostgreSQL `WHERE` clauses to minimize network transfer.
* **`@st.cache_resource`**: Caches un-pickled global connection engines across all web user sessions.
* **`@st.cache_data`**: Caches read-only query DataFrames for a specified time-to-live (`ttl=300` seconds).
* **Decoupled BI UI**: Designing dashboard pages to consume service methods rather than embedding raw SQL strings inside UI files.

---

## 🛠️ Streamlit Commands Reference

```python
st.set_page_config(page_title="RetailLens", layout="wide") # Page layout
st.sidebar.radio("Navigation", options=[...])             # Radio navigation
col1, col2 = st.columns(2)                                # Responsive layout
st.metric(label="Revenue", value="£1.25M")                 # KPI Metric Card
st.plotly_chart(fig, use_container_width=True)             # Plotly Chart
st.dataframe(df, use_container_width=True)                 # Data Table
st.cache_data.clear()                                      # Invalidate Cache
```

---

## 💡 Top 5 Dashboard Interview Talking Points

1. *"We decoupled our Streamlit UI views from the database by consuming `SQLAnalyticsService` methods instead of embedding raw SQL strings inside UI components."*
2. *"We implemented SQL Filter Pushdown, passing sidebar filter choices (`Start Date`, `Country`) into parameterized PostgreSQL queries rather than downloading raw tables and filtering in Python memory."*
3. *"We used `@st.cache_resource` for database engine pooling and `@st.cache_data(ttl=300)` for read query caching, providing sub-second page re-renders while allowing manual cache invalidation via a 'Refresh Data' button."*
4. *"Our dashboard handles database downtime gracefully—displaying user-friendly warnings (`'⚠️ Unable to connect to database'`) without leaking connection credentials or stack traces to end users."*
5. *"We built five dedicated module views (`Overview`, `Sales`, `Products`, `Customers`, `Operations`) with custom Plotly visualizations and responsive KPI metric cards."*
