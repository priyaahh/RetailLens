# 🎯 Master Technical Interview Q&A Bank (Phases 1–5)

This document contains a production-grade interview question bank derived from **Phases 1, 2, 3, 4 & 5**. Use this guide to prepare for technical interview rounds across Data Engineering, Software Engineering, Backend Development, SQL, System Design, DevOps, and Business Intelligence.

---

## 🛠️ 1. Software Engineering & Architecture

### Q1: What is modular architecture, and how is it implemented in RetailLens?
**Model Answer**:
Modular architecture is a design pattern where an application is decomposed into independent, self-contained modules—each responsible for a single business capability. In RetailLens, we separate concerns across distinct directories: `ingestion/` handles data reading and file parsing, `database/` manages database connections and queries, `analytics/` processes metric calculations and ML models, and `app/` controls the UI. This ensures high cohesion within modules and loose coupling between modules, making the system testable and easy to maintain.

### Q2: What is the principle of "Separation of Concerns" (SoC)?
**Model Answer**:
Separation of Concerns is a core software engineering principle stating that a program should be split into distinct sections, with each section addressing a separate concern. In RetailLens, UI code inside `app/` never executes raw SQL queries or data validation routines directly; instead, it calls functions exposed by the `analytics/` and `database/` modules. This prevents UI changes from breaking database operations or data processing pipelines.

---

## 🐘 2. PostgreSQL, Data Modeling & SQL Analytics (Phase 3)

### Q22: What is a Fact Table, a Dimension Table, and the Grain of a fact table?
* **Strong Answer**: A Fact Table (`fact_sales`) contains quantitative numerical measurements (revenue, quantity). A Dimension Table (`dim_customer`, `dim_product`) contains descriptive context attributes. The Grain defines the level of detail of a single row. In RetailLens, the grain of `fact_sales` is **one row per transaction invoice line item**.
* **Keywords**: `Fact Table`, `Dimension Table`, `Table Grain`, `Line-Item Level`.

### Q24: What is the logical execution order of a SQL query, and why does `WHERE` come before `HAVING`?
* **Strong Answer**: SQL queries execute in order: `FROM/JOIN` $\rightarrow$ `WHERE` $\rightarrow$ `GROUP BY` $\rightarrow$ `HAVING` $\rightarrow$ `SELECT` $\rightarrow$ `WINDOW` $\rightarrow$ `ORDER BY` $\rightarrow$ `LIMIT`. `WHERE` filters individual rows **before** aggregation; `HAVING` filters group summaries **after** aggregation.
* **Keywords**: `Logical Execution Order`, `WHERE vs HAVING`, `Pre-aggregation Filtering`.

---

## 💻 3. Analytics Engine, Repository Pattern & BI Architecture (Phase 4)

### Q31: What is the Repository Pattern, and why is it used in RetailLens?
* **Strong Answer**: The Repository Pattern (`AnalyticsRepository`) isolates all database data access queries behind domain methods. It decouples UI components from database schemas, centralizes query parameterization against SQL injection, and enables unit testing using mocks/in-memory SQLite databases without needing an active cloud database connection.
* **Keywords**: `Repository Pattern`, `Data Access Layer`, `Decoupled Architecture`, `Testability`.

### Q32: Why compute summary metrics directly in SQL instead of in-memory Pandas aggregations?
* **Strong Answer**: Executing aggregations inside PostgreSQL (`SUM`, `COUNT`, `AOV`) uses indexed B-Tree scans and returns a single 8-byte scalar result over the wire. In-memory Pandas aggregation requires fetching 500,000 raw transaction rows over the network, wasting bandwidth and saturating server RAM. Direct SQL aggregation achieves a **99.9% reduction in network payload and RAM footprint**.
* **Keywords**: `Database Pushdown`, `SQL Aggregation`, `Network Payload Optimization`.

---

## ⚙️ 4. Production Hardening, Security, CI/CD & Deployment (Phase 5)

### Q41: How do you handle environment configuration safely across development, testing, staging, and production environments?
* **Strong Answer**: We created a centralized configuration engine (`AppConfig` in `config/app_config.py`). Instead of reading loose `os.getenv()` calls across components, `AppConfig` validates configuration types and enforces profile rules (`development`, `testing`, `staging`, `production`). In `production`, `AppConfig` mandates complete database credentials (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) and rejects default dev keys, raising `ConfigurationError` before app startup.
* **Keywords**: `Centralized Configuration`, `Environment Profiles`, `Strict Validation`, `AppConfig`.

### Q42: How do you prevent secret keys and database passwords from being logged or leaked in error stack traces?
* **Strong Answer**: We attach a `SensitiveDataFilter` to all logger handlers in `config/logging_config.py`. The filter uses regex patterns to redact passwords (`password='***MASKED***'`), connection URLs (`postgresql://user:***MASKED***@host`), and secret keys before log entries are written to stdout or `logs/retaillens.log`.
* **Keywords**: `SensitiveDataFilter`, `Credential Masking`, `Log Security`, `Regex Sanitization`.

### Q43: How do you implement exponential backoff retries for transient database failures while failing fast on permanent errors?
* **Strong Answer**: We implemented `execute_with_retry()` in `database/retry.py`. For retryable transient errors (`TransientDatabaseError`, connection timeouts), it retries execution up to 3 times with exponentially increasing delays (0.1s, 0.2s, 0.4s). For non-retryable constraint violations or syntax errors (`PermanentDatabaseError`), it fails fast immediately without executing useless retries.
* **Keywords**: `Exponential Backoff`, `Transient Database Error`, `Fail-Fast`, `Resilience`.

### Q44: How does your path traversal validation prevent malicious file uploads?
* **Strong Answer**: `DataFileReader.validate_file_metadata()` inspects the input file path for path traversal sequences (`..`). If detected, it immediately raises a `ValueError` before opening the path or reading bytes, preventing attackers from reading sensitive system files outside the target directory.
* **Keywords**: `Path Traversal Prevention`, `Input Validation`, `Defensive File Reading`.

### Q45: What is the purpose of the GitHub Actions CI pipeline in RetailLens?
* **Strong Answer**: Our GitHub Actions workflow (`.github/workflows/ci.yml`) triggers automatically on every push or pull request to `main` and `dev`. It sets up Python 3.10, installs dependencies, and runs `python -m unittest discover tests`. If any test fails, the workflow blocks code merging, ensuring broken code never reaches production.
* **Keywords**: `GitHub Actions`, `Continuous Integration`, `Automated Testing`, `Pull Request Gate`.

### Q46: How is RetailLens containerized for production using Docker?
* **Strong Answer**: We authored a multi-stage `Dockerfile` based on `python:3.10-slim`. It sets up working directories, installs system dependencies (`libpq-dev`), copies requirements, exposes port `8501`, and includes an HTTP healthcheck assertion (`curl -f http://localhost:8501/_stcore/health`). `.dockerignore` excludes virtual environments, local logs, secrets, and test artifacts.
* **Keywords**: `Docker Containerization`, `Multi-Stage Build`, `HTTP Healthcheck`, `.dockerignore`.

### Q47: What is the difference between `@st.cache_resource` and `@st.cache_data` in Streamlit?
* **Strong Answer**: `@st.cache_resource` caches global, un-pickled long-lived objects (like SQLAlchemy connection pools or `AnalyticsService` instances) shared across all user sessions. `@st.cache_data(ttl=300)` caches read-only serialized data objects (like query DataFrames) with a 5-minute time-to-live.
* **Keywords**: `@st.cache_resource`, `@st.cache_data`, `Streamlit Caching`, `Time-To-Live`.

### Q48: How would you scale RetailLens to handle multi-terabyte datasets and thousands of concurrent users?
* **Strong Answer**: 
  1. **MPP Data Warehouse**: Migrate PostgreSQL storage to a columnar data warehouse (Snowflake / BigQuery).
  2. **dbt Semantic Modeling**: Pre-compute analytical models and materialized views using dbt.
  3. **FastAPI Microservice + Redis**: Move `AnalyticsService` to a standalone FastAPI REST microservice backed by Redis caching.
  4. **Horizontal Pod Autoscaling**: Deploy Streamlit and API containers on Kubernetes behind an AWS ALB load balancer.
* **Keywords**: `Snowflake`, `dbt`, `FastAPI Microservice`, `Redis Cache`, `Kubernetes HPA`.
