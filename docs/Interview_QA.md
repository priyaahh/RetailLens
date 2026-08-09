# 🎯 Master Technical Interview Q&A Bank

This document contains a production-grade interview question bank derived from **Phases 1, 2, 3 & 4**. Use this guide to prepare for technical interview rounds across Data Engineering, Software Engineering, Backend Development, SQL, System Design, and Business Intelligence.

---

## 🛠️ 1. Software Engineering & Architecture

### Q1: What is modular architecture, and how is it implemented in RetailLens?
**Model Answer**:
Modular architecture is a design pattern where an application is decomposed into independent, self-contained modules—each responsible for a single business capability. In RetailLens, we separate concerns across distinct directories: `ingestion/` handles data reading and file parsing, `database/` manages database connections and queries, `analytics/` processes metric calculations and ML models, and `app/` controls the UI. This ensures high cohesion within modules and loose coupling between modules, making the system testable and easy to maintain.

---

## 💻 2. Analytics Engine, Repository Pattern & BI Architecture (Phase 4)

### Q31: What is the Repository Pattern, and why is it used in RetailLens?
* **Strong Answer**: 
  The **Repository Pattern** abstracts database data access behind a clean domain interface (`AnalyticsRepository`). In RetailLens, it isolates all SQL query execution, parameterization, and SQLAlchemy connection logic from the application service and UI layers. This decouples UI view components from database schemas and enables unit testing analytics code using mocks or in-memory SQLite databases without needing an active cloud database connection.
* **Keywords**: `Repository Pattern`, `Data Access Layer`, `Decoupled Architecture`, `Testability`.
* **Possible Follow-up**: *How do you pass UI filter selections to your repository methods?*

---

### Q32: Why compute summary metrics directly in SQL instead of doing in-memory Pandas aggregations?
* **Strong Answer**: 
  Executing aggregations directly inside PostgreSQL (`SUM`, `COUNT`, `AOV`) uses indexed B-Tree scans and returns a single 8-byte scalar result or a small summary dataset over the network. In-memory Pandas aggregation requires fetching 500,000 raw transaction line items over the wire first, wasting network bandwidth, saturating web server RAM, and creating Out-of-Memory (OOM) crash risks. Direct SQL aggregation achieves a **99.9% reduction in network payload and RAM footprint**.
* **Keywords**: `Database Pushdown`, `SQL Aggregation`, `Network Payload Optimization`, `RAM Footprint`.

---

### Q33: How does the `InsightEngine` generate automated business observations?
* **Strong Answer**: 
  `InsightEngine` evaluates calculated KPI metrics and repository summary DataFrames against configurable operational risk thresholds (e.g. `cancellation_rate >= 5.0%`, `guest_ratio >= 40.0%`). When a metric crosses a threshold, the engine constructs a structured `Insight` dataclass containing the category (`CANCELLATION`, `TREND`, `PRODUCT`), title, description, severity level (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), metric value, threshold limit, and an actionable business recommendation.
* **Keywords**: `Insight Engine`, `Threshold Evaluation`, `Structured Observations`, `Severity Levels`, `Actionable Recommendations`.

---

### Q34: What is the role of the `AnalyticsService` layer?
* **Strong Answer**: 
  `AnalyticsService` acts as the Application Service Layer facade between PostgreSQL data access and the Streamlit UI. It composes `AnalyticsRepository` data queries, `KPIEngine` metric calculations, and `InsightEngine` observations into high-level business methods (`get_dashboard_summary()`, `get_cancellation_analysis()`). Streamlit UI components call these service methods exclusively, adhering strictly to **Separation of Concerns (SoC)**.
* **Keywords**: `Application Service Layer`, `Facade Pattern`, `Separation of Concerns`, `Orchestration`.

---

### Q35: How does Streamlit caching work, and what is the difference between `@st.cache_resource` and `@st.cache_data`?
* **Strong Answer**: 
  Streamlit re-runs Python scripts top-to-bottom on every user interaction. Caching prevents re-executing heavy database queries or connection setups:
  * `@st.cache_resource`: Caches global, un-pickled, long-lived resources (like SQLAlchemy database engines or `AnalyticsService` instances) shared across all user sessions.
  * `@st.cache_data`: Caches serialized data objects (like query DataFrames) with a configurable time-to-live (`ttl=300` seconds).
* **Keywords**: `@st.cache_resource`, `@st.cache_data`, `Time-To-Live (TTL)`, `Script Execution Cycle`.

---

### Q36: What is SQL Filter Pushdown, and why is it essential for dashboard performance?
* **Strong Answer**: 
  SQL Filter Pushdown passes user sidebar filter choices (`Start Date`, `Country`, `Customer Type`) directly into parameterized PostgreSQL SQL queries (`WHERE country = :country AND invoice_timestamp >= :start_date`). This forces PostgreSQL to execute filtering at the database layer, returning only matching summary datasets over the network rather than downloading raw tables and filtering in Python memory.
* **Keywords**: `SQL Pushdown`, `Parameterized WHERE Clauses`, `Network Latency`, `RAM Optimization`.

---

### Q37: How do you unit test a database-dependent analytics service without requiring a live Neon cloud database?
* **Strong Answer**: 
  We use **Mock Objects** (`unittest.mock.MagicMock`) and **In-Memory SQLite Databases** (`sqlite:///:memory:`). Unit tests inject mock repositories into `KPIEngine`, `InsightEngine`, and `AnalyticsService`, returning deterministic test DataFrames or scalars to verify calculation formulas and threshold logic instantly in local CI/CD pipelines without network or cloud database dependencies.
* **Keywords**: `Mock Objects`, `In-Memory SQLite`, `Unit Testing`, `Dependency Injection`, `CI/CD`.

---

### Q38: How does your dashboard handle database downtime or connection failures?
* **Strong Answer**: 
  Our main application entry point (`app/main.py`) wraps service initialization and query calls inside defensive `try/except` blocks. If PostgreSQL is unavailable or credentials are bad, Streamlit catches the error, logs the stack trace internally, and displays a user-friendly error card (`"⚠️ Unable to connect to database. Please check configuration"`). This prevents exposing database connection strings, passwords, or technical stack traces to end users.
* **Keywords**: `Graceful Error Handling`, `Defensive Exception Catching`, `Credential Masking`, `User Experience`.

---

### Q39: How do `COALESCE` and `NULLIF` prevent runtime errors in SQL KPI metrics?
* **Strong Answer**: 
  `COALESCE(val, fallback)` replaces `NULL` query results with a default value (e.g., `COALESCE(SUM(total_amount), 0.00)` returns `0.00` on an empty database). `NULLIF(val1, val2)` returns `NULL` when `val1 == val2`. Placing `NULLIF(COUNT(DISTINCT invoice_no), 0)` in denominator division calculations prevents catastrophic **division-by-zero** database runtime exceptions when tables contain zero rows.
* **Keywords**: `COALESCE`, `NULLIF`, `Division-by-Zero Protection`, `Defensive SQL`.

---

### Q40: How would you scale the analytics architecture from a single PostgreSQL database to an enterprise data platform?
* **Strong Answer**: 
  To scale to petabyte datasets and thousands of concurrent BI users:
  1. **Semantic Layer (dbt / Cube.js)**: Introduce **dbt** (data build tool) to model raw warehouse data into star-schema analytical tables and pre-computed materialized views.
  2. **Cloud Data Warehouse (Snowflake / BigQuery)**: Replace single-node PostgreSQL with a columnar cloud data warehouse for massively parallel processing (MPP) analytical queries.
  3. **REST / GraphQL Analytics API**: Wrap `AnalyticsService` inside a FastAPI web service, exposing cached JSON endpoints consumed by multiple frontend clients (Streamlit, React, mobile apps).
* **Keywords**: `dbt Semantic Layer`, `Snowflake Data Warehouse`, `MPP Architecture`, `FastAPI Analytics Microservice`.
