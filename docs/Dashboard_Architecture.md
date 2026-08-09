# 📐 Dashboard Architecture & Performance Design

This document details the architectural design, component hierarchy, state management, and performance caching strategy of the **RetailLens Streamlit Analytics Dashboard**.

---

## 🏛️ 1. Layered Architecture Overview

The dashboard follows a strict **Layered Architecture Pattern**:

```text
View Layer (app/pages/)
        │ Consumes Component Layouts
        ▼
Component Layer (app/components/)
        │ Calls Analytics Methods
        ▼
Analytics Layer (analytics/)
        │ Executes Parameterized SQL Queries
        ▼
Database Layer (database/ & PostgreSQL)
```

### Architectural Rule: Decoupled UI from SQL
The Streamlit View layer contains **zero raw SQL queries**. 

* ❌ **Bad (Tightly Coupled)**:
  ```python
  # Streamlit UI page writing raw SQL
  df = pd.read_sql("SELECT SUM(total_amount) FROM fact_sales", engine)
  st.write(df)
  ```
* ✅ **Good (Decoupled & Testable)**:
  ```python
  # Streamlit UI page consuming service method
  revenue = kpi_calc.total_revenue(start_date=start, country=country)
  st.metric("Total Revenue", format_currency(revenue))
  ```

---

## ⚡ 2. Caching Strategy & State Management

### A. `@st.cache_resource` vs `@st.cache_data`

| Cache Decorator | Purpose | Retained Object | RetailLens Usage |
| :--- | :--- | :--- | :--- |
| **`@st.cache_resource`** | Global, un-pickled long-lived resources. Shared across all user sessions. | SQLAlchemy Engine, `KPICalculator`, `SQLAnalyticsService` | `init_database_services()` in `main.py` |
| **`@st.cache_data`** | Serialized data objects. Invalidates after TTL or input change. | Pandas DataFrames, Country lists | `fetch_country_list()` (TTL = 300 seconds) |

---

## 🎛️ 3. SQL Filter Pushdown Strategy

When a user selects filters in the sidebar (e.g. `Country = "France"`, `Start Date = "2010-12-01"`):
1. Filters are captured as a dictionary in `filters.py`.
2. Filter dictionary is passed to `SQLAnalyticsService` or `KPICalculator`.
3. `_build_where_clause()` constructs parameterized SQL `WHERE` conditions (`WHERE country = :country AND invoice_timestamp >= :start_date`).
4. **PostgreSQL executes filtering at the database layer**, returning only matching summary rows over the network.

This **SQL Pushdown Strategy** avoids downloading multi-gigabyte raw tables into Streamlit web server RAM, protecting against memory overflow and optimizing latency.
