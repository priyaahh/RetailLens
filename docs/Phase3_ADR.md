# 🏗️ Phase 3 Architectural Decision Records (ADR)

This document records the architectural and design decisions made for the **RetailLens SQL Business Analytics & PostgreSQL Integration Layer** (Phase 3).

---

## 📌 ADR 010: Managed Cloud PostgreSQL as Analytical Database Layer

* **Decision**: Store clean fact tables and execute analytical queries in Neon Cloud PostgreSQL.
* **Context**: Need a relational database storage layer to support SQL analytics, window functions, and Streamlit dashboard backend querying.
* **Options Considered**:
  1. Local SQLite file database.
  2. Cloud PostgreSQL (Neon).
  3. Cloud Data Warehouse (Snowflake / BigQuery).
* **Chosen Approach**: Neon Cloud PostgreSQL.
* **Why**: Provides production-grade ANSI SQL capability, B-Tree index support, window functions, connection pooling, and cloud hosting for zero infrastructure cost.
* **Trade-offs**: Single-node row-oriented DB limits execution speed on petabyte-scale datasets.
* **Future Improvements**: Migrate to Snowflake if dataset scales past 50GB.

---

## 📌 ADR 011: Denormalized Fact Table (`fact_sales`) with Analytical Views for MVP Scope

* **Decision**: Primary analytical model centers on a rich denormalized fact table (`fact_sales`) backed by dimension tables (`dim_customer`, `dim_product`) and database views.
* **Context**: Deciding between a 5-table Star Schema versus a single denormalized fact table.
* **Options Considered**:
  1. Highly normalized 3NF relational schema.
  2. Pure Star Schema with mandatory foreign key joins on every query.
  3. Denormalized fact table with dimension reference tables and analytical views.
* **Chosen Approach**: Denormalized fact table with dimension views.
* **Why**: Eliminates expensive multi-table `JOIN` overhead on simple aggregated queries, accelerating Streamlit UI chart execution while retaining dimensional attributes.
* **Trade-offs**: Slightly larger table storage footprint due to string columns (`country`, `description`).
* **Future Improvements**: Enforce strict foreign key constraints between `fact_sales` and dimension tables as user volume grows.

---

## 📌 ADR 012: SQL Database Computation over In-Memory Pandas Aggregation for KPIs

* **Decision**: Compute executive KPIs (`KPICalculator`) directly inside PostgreSQL using SQL queries rather than loading raw tables into Pandas memory.
* **Context**: Deciding where summary KPI aggregations should execute.
* **Options Considered**:
  1. Fetch full `fact_sales` table into Pandas memory and run `df['total_amount'].sum()`.
  2. Execute `SELECT SUM(total_amount) FROM fact_sales` in PostgreSQL via SQLAlchemy.
* **Chosen Approach**: Direct SQL Aggregation in PostgreSQL.
* **Why**: PostgreSQL returns a single 8-byte scalar result over the network instead of transferring 500,000 raw rows to Python, reducing network I/O and RAM usage by 99.9%.
* **Trade-offs**: Requires writing explicit SQL query strings.
* **Future Improvements**: Pre-calculate KPIs into PostgreSQL materialized views refreshed on pipeline completion.

---

## 📌 ADR 013: Parameterized SQL Queries in `SQLAnalyticsService`

* **Decision**: Execute all SQL queries via SQLAlchemy `text()` using parameterized bindings (`params={"limit_val": limit}`).
* **Context**: Protecting database execution against SQL injection vulnerabilities.
* **Options Considered**:
  1. String concatenation (`f"SELECT * FROM fact_sales LIMIT {limit}"`).
  2. Parameterized SQL binding (`text("SELECT ... LIMIT :limit_val")`).
* **Chosen Approach**: Parameterized SQL binding.
* **Why**: Prevents **SQL Injection** attacks completely by separating SQL code parsing from user input values.
* **Trade-offs**: Requires passing parameter dictionaries.
* **Future Improvements**: Implement static query linting (e.g. `sqlfluff`) in CI/CD pipelines.

---

## 📌 ADR 014: Native Window Functions over Multi-Stage Self-Joins for MoM Analytics

* **Decision**: Calculate Month-over-Month (MoM) revenue growth using native `LAG()` window functions inside CTEs.
* **Context**: Calculating growth rates requires comparing current month revenue with previous month revenue.
* **Options Considered**:
  1. Self-joining the monthly summary table on `m1.month = m2.month + 1`.
  2. `LAG(revenue, 1) OVER (ORDER BY invoice_year, invoice_month)`.
* **Chosen Approach**: Native `LAG()` Window Function.
* **Why**: Executes in a single sequential scan pass over sorted data without multi-table join computational overhead.
* **Trade-offs**: Requires PostgreSQL or database engines supporting ANSI window functions.
* **Future Improvements**: Add `LEAD()` functions to calculate forward-looking sales trajectory projections.
