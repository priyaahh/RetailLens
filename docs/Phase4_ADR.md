# 🏗️ Phase 4 Architectural Decision Records (ADR)

This document records the key architectural decisions for the **RetailLens Analytics Engine & Business Intelligence Layer** (Phase 4).

---

## 📌 ADR 015: Repository Pattern for Data Access

* **Decision**: Implement `AnalyticsRepository` to isolate all PostgreSQL database calls behind domain methods.
* **Context**: Streamlit UI components require analytics data without embedding raw SQL strings or managing database connections directly.
* **Options Considered**:
  1. Writing raw `pd.read_sql()` strings inside Streamlit page scripts.
  2. Direct ORM model queries inside UI view files.
  3. `AnalyticsRepository` class encapsulating SQL data access.
* **Chosen Approach**: `AnalyticsRepository` class.
* **Why**: Completely decouples UI view code from SQL execution, enables unit testing using mocks/in-memory SQLite, and centralizes parameterization against SQL injection.
* **Trade-offs**: Requires creating repository class abstraction methods.

---

## 📌 ADR 016: Direct Database Aggregation over In-Memory Pandas Computation

* **Decision**: Compute summary metrics (`SUM`, `COUNT`, `AOV`) inside PostgreSQL using SQL queries rather than transferring raw tables into Pandas memory.
* **Context**: Deciding where summary KPI aggregations should execute.
* **Options Considered**:
  1. Transfer 500,000 raw transaction line items into Pandas RAM and run `df['total_amount'].sum()`.
  2. Execute `SELECT SUM(total_amount) FROM fact_sales` in PostgreSQL.
* **Chosen Approach**: Direct SQL Aggregation in PostgreSQL.
* **Why**: PostgreSQL returns a single 8-byte scalar result over the network instead of transferring 500,000 raw rows to Python, reducing network I/O and RAM usage by 99.9%.
* **Trade-offs**: Requires writing explicit SQL aggregation queries.

---

## 📌 ADR 017: Structured Business Insight Generation Engine

* **Decision**: Implement `InsightEngine` generating structured `Insight` objects with severity levels, metrics, thresholds, and actionable recommendations.
* **Context**: Business users require actionable narrative observations alongside numerical chart visualisations.
* **Options Considered**:
  1. Displaying raw static text bullet points in UI.
  2. Returning unstructured string logs.
  3. Structured `Insight` dataclass objects evaluated against configurable thresholds.
* **Chosen Approach**: Structured `Insight` objects.
* **Why**: Enables severity filtering, standardized UI alert card rendering, and configurable operational risk thresholds.
* **Trade-offs**: Requires maintaining threshold configuration parameters.

---

## 📌 ADR 018: Two-Tier Streamlit Caching Strategy

* **Decision**: Use `@st.cache_resource` for global `AnalyticsService` objects and `@st.cache_data(ttl=300)` for read query DataFrames.
* **Context**: Streamlit re-runs scripts top-to-bottom on every user interaction, risking repeated database queries.
* **Options Considered**:
  1. No caching (queries PostgreSQL on every click).
  2. Unbounded `@st.cache_data` without TTL.
  3. Two-tier caching with 5-minute TTL and manual cache clear button.
* **Chosen Approach**: Two-tier caching with 5-minute TTL and manual clear button.
* **Why**: Eliminates redundant database roundtrips, delivers sub-second page switches, and allows users to manually force-refresh data when fresh ETL batches land.
* **Trade-offs**: Data updates landing during the 5-minute TTL window require manual cache refresh.
