# 📖 Phase 3: SQL Business Analytics & PostgreSQL Integration — Final Revision Notes

This document is the **definitive, source-of-truth technical study guide and architectural reference** for **Phase 3** of the **RetailLens** platform. It documents the relational schema design, analytical SQL queries, advanced SQL (CTEs, Window Functions), Python $\leftrightarrow$ PostgreSQL integration, KPI engines, query performance indexing, and technical interview preparation.

---

## 🏛️ 1. Complete Phase 3 System Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             CLIENT BROWSER / UI                                  │
│  Interactive Streamlit Dashboard / Power BI Executive Reports                    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │  Calls Python Analytics Service Layer
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      ANALYTICS SERVICE & KPI LAYER (analytics/)                  │
│  ┌─────────────────────────┐                 ┌─────────────────────────────────┐ │
│  │   SQLAnalyticsService   │ ──────────────► │          KPICalculator          │ │
│  │  (sql_analytics.py)     │                 │            (kpis.py)            │ │
│  └────────────┬────────────┘                 └────────────────┬────────────────┘ │
└───────────────┼───────────────────────────────────────────────┼──────────────────┘
                │                                               │
                │ Executes Parameterized SQL Queries            │ Direct SQL Aggregation
                ▼                                               ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                      MASTER SQL ANALYTICS CATALOG (queries.sql)                  │
│  25 Core & Advanced Queries (CTEs, Window Functions, MoM Growth, Leaderboards)   │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │  SQLAlchemy Engine Connection Pool
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     DATABASE CONNECTION LAYER (connection.py)                    │
│  SQLAlchemy Engine (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`)      │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │  TCP / IP over Encrypted TLS/SSL (Port 5432)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     MANAGED CLOUD POSTGRESQL (Neon Cloud DB)                     │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                    RELATIONAL ANALYTICAL MODEL SCHEMA                      │  │
│  │  fact_sales (Fact Table) ◄──► dim_customer (Dim) ◄──► dim_product (Dim)    │  │
│  │  Views: view_monthly_sales_summary, view_top_products                      │  │
│  │  Indexes: idx_fact_sales_invoice_no, idx_fact_sales_customer_id,           │  │
│  │           idx_fact_sales_timestamp,  idx_fact_sales_year_month           │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 2. Database Schema & Dimensional Data Modeling (Milestone 1)

### Dimensional Data Modeling Concepts
* **Fact Table (`fact_sales`)**: Stores quantitative, numerical business measurements (sales revenue, units sold, unit prices). Grain: **One row per invoice line item**.
* **Dimension Tables (`dim_customer`, `dim_product`)**: Stores descriptive attributes (customer type, country, product descriptions) giving context to fact metrics.
* **Star Schema**: Dimensional modeling technique surrounding a central fact table with denormalized dimension tables linked via surrogate keys.
* **Surrogate Key vs Natural Key**:
  * *Surrogate Key (`transaction_id`, `customer_key`)*: System-generated integer primary key (`BIGSERIAL`) created exclusively for efficient indexing and joining.
  * *Natural/Business Key (`invoice_no`, `stock_code`, `customer_id`)*: Identifier assigned by operational retail systems.

### PostgreSQL DDL Schema (`database/schema.sql`)

```sql
-- Processed Analytics Fact Table
CREATE TABLE fact_sales (
    transaction_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity != 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0.00),
    total_amount NUMERIC(12,2) NOT NULL,
    invoice_timestamp TIMESTAMP NOT NULL,
    invoice_year SMALLINT NOT NULL,
    invoice_month SMALLINT NOT NULL CHECK (invoice_month BETWEEN 1 AND 12),
    invoice_quarter SMALLINT NOT NULL CHECK (invoice_quarter BETWEEN 1 AND 4),
    day_of_week VARCHAR(10) NOT NULL,
    invoice_hour SMALLINT NOT NULL CHECK (invoice_hour BETWEEN 0 AND 23),
    customer_id VARCHAR(20) NOT NULL DEFAULT 'GUEST',
    customer_type VARCHAR(20) NOT NULL DEFAULT 'Guest',
    country VARCHAR(50) NOT NULL,
    is_cancellation BOOLEAN NOT NULL DEFAULT FALSE,
    revenue_bucket VARCHAR(30) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔍 3. Core Business & Advanced SQL Analytics Catalog (Milestones 2 & 3)

Located in [`database/queries.sql`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/database/queries.sql), containing 25 queries.

### Core Business Query Highlights (Milestone 2)
* **Average Order Value (AOV)**:
  ```sql
  SELECT ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS aov
  FROM fact_sales WHERE is_cancellation = FALSE;
  ```
* **Cancellation Rate %**:
  ```sql
  SELECT ROUND((COUNT(DISTINCT CASE WHEN is_cancellation = TRUE THEN invoice_no END)::NUMERIC / 
                NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2) AS cancellation_rate_pct
  FROM fact_sales;
  ```

### Advanced SQL Analytical Highlights (Milestone 3)
* **Month-over-Month (MoM) Growth Rate (CTE + `LAG()` Window Function)**:
  ```sql
  WITH monthly_revenue AS (
      SELECT invoice_year, invoice_month, SUM(total_amount) AS revenue
      FROM fact_sales WHERE is_cancellation = FALSE
      GROUP BY invoice_year, invoice_month
  )
  SELECT 
      invoice_year, invoice_month, revenue,
      LAG(revenue, 1) OVER (ORDER BY invoice_year, invoice_month) AS prev_month_revenue,
      ROUND(((revenue - LAG(revenue, 1) OVER (ORDER BY invoice_year, invoice_month)) / 
             NULLIF(LAG(revenue, 1) OVER (ORDER BY invoice_year, invoice_month), 0)) * 100, 2) AS mom_growth_pct
  FROM monthly_revenue;
  ```
* **Top 3 Products per Country (`DENSE_RANK()` Window Function)**:
  ```sql
  WITH ranked_products AS (
      SELECT country, stock_code, description, SUM(total_amount) AS revenue,
             DENSE_RANK() OVER (PARTITION BY country ORDER BY SUM(total_amount) DESC) AS rank
      FROM fact_sales WHERE is_cancellation = FALSE
      GROUP BY country, stock_code, description
  )
  SELECT country, rank, stock_code, description, revenue
  FROM ranked_products WHERE rank <= 3;
  ```

---

## 🐍 4. Python Analytics & KPI Layer (Milestones 4 & 5)

* **`SQLAnalyticsService` ([`analytics/sql_analytics.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/sql_analytics.py))**: Decouples UI from database queries. Executes SQL queries via SQLAlchemy engine connection pooling and returns clean DataFrames for Streamlit and Plotly.
* **`KPICalculator` ([`analytics/kpis.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/kpis.py))**: Executes scalar single-query aggregations directly in PostgreSQL (`total_revenue()`, `average_order_value()`, `cancellation_rate()`). Uses `COALESCE` and `NULLIF` to prevent division-by-zero or empty-database exceptions.

---

## ⚡ 5. Query Performance & Indexing (Milestone 6)

Detailed in [`docs/SQL_Performance_Notes.md`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/SQL_Performance_Notes.md):
* **B-Tree Indexes**: Created on high-cardinality join/filter columns (`invoice_no`, `customer_id`, `invoice_timestamp`, `country`).
* **Composite Index**: `idx_fact_sales_year_month` ON `fact_sales(invoice_year, invoice_month)` accelerates monthly revenue queries without full table scans.
* **`EXPLAIN ANALYZE`**: Evaluates true execution timing and scan types (Index Only Scan vs Bitmap Index Scan vs Seq Scan).

---

## 🧪 6. Testing Strategy & Data Correctness (Milestone 7)

Tested in [`tests/test_sql_analytics.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/tests/test_sql_analytics.py) and [`tests/test_kpis.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/tests/test_kpis.py) using SQLite in-memory fixtures:
* Verifies revenue calculations, order counts, AOV, cancellation rates, top product lookup, and empty-database behavior.

---

## 📊 7. Architectural Decision Record (Phase 3 ADR)

| Decision | Chosen Approach | Why Selected | Alternative | When Alternative Makes Sense |
| :--- | :--- | :--- | :--- | :--- |
| **Analytical Model** | Denormalized Fact Table (`fact_sales`) with Dimension Views | Accelerates single-table aggregations for MVP scope (<2GB) without multi-table join overhead. | Full Star Schema with 5 Normalized Dimension Tables | Enterprise data warehouses with millions of dimension attributes. |
| **SQL vs Pandas Analytics** | SQL Execution in Database (`KPICalculator`) | Executing aggregations inside PostgreSQL processes only bytes of summary data over network. | Pulling 500,000 raw rows into Pandas memory | Complex non-SQL machine learning model training pipelines. |
| **Window Functions** | Native PostgreSQL Window Functions (`DENSE_RANK()`, `LAG()`) | Pre-calculates MoM growth and rankings in single SQL passes without multi-query joins. | Multiple self-joins in SQL | Legacy relational databases lacking window function support. |

---

## ❓ 8. Master Interview Questions (Phase 3)

### Q1: What is the difference between an OLTP database and an OLAP data warehouse?
* **Strong Answer**: OLTP databases (like PostgreSQL) use row-oriented storage optimized for ACID-compliant, low-latency transactional writes and row lookups. OLAP data warehouses (like Snowflake or BigQuery) use columnar storage optimized for reading specific columns across billions of rows during analytical aggregations.
* **Keywords**: `OLTP vs OLAP`, `Row vs Columnar Storage`, `ACID Compliance`, `Aggregation Efficiency`.

### Q2: What is the difference between `WHERE` and `HAVING` in SQL?
* **Strong Answer**: `WHERE` filters individual rows **before** `GROUP BY` aggregation occurs. `HAVING` filters aggregated group summaries **after** `GROUP BY` execution.
* **RetailLens Example**: `WHERE is_cancellation = FALSE GROUP BY customer_id HAVING SUM(total_amount) > 1000`.
* **Keywords**: `WHERE vs HAVING`, `Row-level vs Group-level Filtering`, `Execution Order`.

### Q3: Explain how `RANK()`, `DENSE_RANK()`, and `ROW_NUMBER()` handle ties.
* **Strong Answer**: For tied values (e.g. two customers with equal $1,000 spend):
  * `ROW_NUMBER()` assigns sequential unique integers arbitrarily (1, 2, 3).
  * `RANK()` assigns identical ranks with rank gaps (1, 1, 3).
  * `DENSE_RANK()` assigns identical ranks without rank gaps (1, 1, 2).
* **Keywords**: `Window Functions`, `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `Tie Handling`.

---

## ⚡ 9. 5-Minute Phase 3 Cheat Sheet

* **AOV Formula**: `SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0)`.
* **Cancellation Rate Formula**: `(COUNT(DISTINCT CASE WHEN is_cancellation = TRUE THEN invoice_no END)::NUMERIC / NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100`.
* **MoM Growth Formula**: `((current_revenue - LAG(current_revenue) OVER (...)) / NULLIF(LAG(current_revenue) OVER (...), 0)) * 100`.
* **SQL Execution Order**: `FROM` $\rightarrow$ `WHERE` $\rightarrow$ `GROUP BY` $\rightarrow$ `HAVING` $\rightarrow$ `SELECT` $\rightarrow$ `WINDOW` $\rightarrow$ `ORDER BY` $\rightarrow$ `LIMIT`.
