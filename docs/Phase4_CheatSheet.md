# ⚡ Phase 4 Cheat Sheet (5-Minute Analytics & BI Revision Guide)

---

## 📐 Architecture Flow

```text
Streamlit UI  ──►  AnalyticsService  ──►  KPIEngine & InsightEngine  ──►  AnalyticsRepository  ──►  PostgreSQL
```

---

## 🔑 Key Layer Definitions

* **AnalyticsRepository**: Data access abstraction executing parameterized SQL queries in PostgreSQL and returning DataFrames or scalar values.
* **KPIEngine**: Composes repository results into structured `KPIMetric` objects with business definitions and zero-division protection (`NULLIF`).
* **InsightEngine**: Evaluates metrics against configurable business thresholds (`cancellation_rate_threshold=5.0%`) to generate structured `Insight` objects with severity badges and recommendations.
* **AnalyticsService**: Master application service orchestrating repository, KPI, and insight engines for the Streamlit UI layer.
* **SQL Pushdown**: Passing sidebar filter choices directly into PostgreSQL `WHERE` clauses to minimize network transfer.

---

## 🛠️ Streamlit Performance Caching Reference

* **`@st.cache_resource`**: Caches persistent service objects (`AnalyticsService`) and database connection pools globally across all user sessions.
* **`@st.cache_data(ttl=300)`**: Caches read-only query DataFrames for 5 minutes (300 seconds).
* **`st.cache_data.clear()`**: Invalidates cached DataFrames on manual `"🔄 Refresh Data Cache"` button click.

---

## 💡 Top 5 Phase 4 Interview Talking Points

1. *"We implemented the Repository Pattern (`AnalyticsRepository`) to isolate all database SQL execution from frontend Streamlit UI code."*
2. *"We use SQL Aggregation over Pandas Aggregation, computing sums, counts, and AOV inside PostgreSQL to reduce network transfer by 99.9%."*
3. *"Our `InsightEngine` automatically detects operational risks (e.g. cancellation rate > 5%), generating structured `Insight` objects with severity alerts and recommendations."*
4. *"We implemented two-tier caching: `@st.cache_resource` for connection pools and `@st.cache_data(ttl=300)` for read query DataFrames."*
5. *"We built unit tests using mocked repositories and in-memory SQLite instances, verifying KPI formulas and insight thresholds without requiring a live cloud database."*
