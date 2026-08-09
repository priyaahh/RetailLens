# 🚀 RetailLens – End-to-End Retail Analytics Platform

RetailLens is a production-grade retail analytics platform built with Python, PostgreSQL, Streamlit, and Power BI. It ingests raw transaction datasets, executes automated schema and data quality validation, runs a modular ETL pipeline, stores structured fact tables in a cloud PostgreSQL database, and exposes an advanced SQL analytics engine, executive business KPIs, and an interactive Streamlit web dashboard.

---

## ✨ Project Highlights

* 🔄 **End-to-End ETL Pipeline**: Modular Python orchestrator (`ETLPipeline`) coordinating extraction, validation, cleaning, feature engineering, and staging.
* 🛡️ **Data Validation & Quality Checks**: Schema enforcement, null detection, invalid data flagging, and quality metric reports (`ValidationReport`).
* 🐘 **Cloud PostgreSQL Database**: Managed relational database (Neon PostgreSQL) hosting dimensional fact models (`fact_sales`, `dim_customer`, `dim_product`).
* 📊 **Master SQL Analytics Catalog**: 25 business and advanced SQL queries utilizing aggregations, CTEs, window functions (`DENSE_RANK()`, `LAG()`), and date analytics.
* 📈 **Python Analytics & KPI Engine**: `SQLAnalyticsService` and `KPICalculator` executing direct SQL aggregations with protection against division-by-zero (`NULLIF`, `COALESCE`).
* 💻 **Interactive Streamlit Dashboard**: 5-page web application featuring responsive KPI cards, dynamic Plotly charts, interactive filters, SQL filter pushdown, and query caching (`@st.cache_data`).
* 📈 **Power BI Executive Reporting**: Complementary C-suite dashboard for high-level business intelligence.
* 🤖 **Sales Forecasting**: Predictive baseline modeling powered by `scikit-learn`.
* ☁️ **Cloud Deployment**: Hosted live on Streamlit Community Cloud with cloud-hosted database connectivity.
* 🧱 **Modular Architecture**: Clean separation of concerns following SOLID software engineering principles.
* 📚 **Professional Documentation**: Comprehensive design records, data dictionaries, ADR matrices, performance guides, and interview prep books.

---

## 📚 Technical Documentation & Study Guides

Detailed technical notes, architectural decision records (ADR), and technical interview preparation materials are organized in the [`docs/`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs) directory:

* 📄 [**Phase 1 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase1_Notes.md) – Architecture learning summary, ADR matrix, common setup mistakes, and 5-minute interview cheat sheet.
* 📄 [**Phase 2 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase2_Notes.md) – Ingestion, Data Quality Validation Engine, Data Cleaning, Feature Engineering, and Pipeline Orchestration *(Completed)*.
* 📄 [**Phase 3 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase3_Notes.md) – PostgreSQL Relational Schema, Master SQL Catalog, Window Functions, KPI Engine, and SQL Performance *(Completed)*.
* 📄 [**Phase 4 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase4_Notes.md) – Streamlit Web App Architecture, UI Components, Plotly Visualizations, and Caching *(Completed)*.
* 📄 [**Dashboard Architecture**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Dashboard_Architecture.md) – Decoupled UI Design, SQL Filter Pushdown, and Caching Strategy.
* 📄 [**Dashboard Cheat Sheet**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Dashboard_CheatSheet.md) – 5-minute revision cheat sheet for Streamlit and dashboard architecture.
* 📄 [**Interview Q&A Guide**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Interview_QA.md) – Master Q&A bank across Software Engineering, Git, Python, Databases, SQL, Networks, Data Engineering, Dashboard Architecture, and System Design.
* 📄 [**SQL Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/SQL_Notes.md) – SQL syntax reference, execution order, window functions, and date analytics.
* 📄 [**SQL Performance Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/SQL_Performance_Notes.md) – PostgreSQL indexing strategy, B-Tree mechanics, and `EXPLAIN ANALYZE` execution plan analysis.

---

## 📐 System Architecture & Network Flow

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT BROWSER                                    │
│  User visits https://retaillens.streamlit.app                                    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │  HTTP/2 & WebSocket (wss:// Port 443)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         STREAMLIT COMMUNITY CLOUD                                │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │               STREAMLIT WEB APPLICATION ROUTER (app/main.py)               │  │
│  │  Multi-Page View Router  ◄──► Sidebar Filters  ◄──► Plotly Chart Engine    │  │
│  │  Pages: Overview, Sales, Products, Customers, Operations                   │  │
│  └─────────────────────────────────────┬──────────────────────────────────────┘  │
│                                        │ Internal Function Calls                 │
│                                        ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION ETL & ANALYTICS LAYER                       │  │
│  │  ETLPipeline ──► SQLAnalyticsService ──► KPICalculator (analytics/)        │  │
│  └─────────────────────────────────────┬──────────────────────────────────────┘  │
└────────────────────────────────────────┼─────────────────────────────────────────┘
                                         │  TCP / IP over TLS / SSL (Port 5432)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        NEON POSTGRESQL (MANAGED CLOUD DB)                        │
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

## 📊 Data Dictionary (Online Retail Dataset)

### Processed Analytics Schema: `fact_sales`

| Column Name | Target DB Type | Constraint | Derived / Feature Engineering Logic |
| :--- | :--- | :--- | :--- |
| `transaction_id` | `BIGSERIAL` | `PRIMARY KEY` | Auto-incrementing surrogate primary key. |
| `invoice_no` | `VARCHAR(20)` | `NOT NULL` | Stripped of whitespace, uppercase normalized. |
| `stock_code` | `VARCHAR(20)` | `NOT NULL` | Cleaned product identifier. |
| `description` | `TEXT` | `NOT NULL` | Imputed string (`'UNKNOWN DESCRIPTION'` if original was null). |
| `quantity` | `INTEGER` | `NOT NULL CHECK (!= 0)`| Cleaned unit count. |
| `unit_price` | `NUMERIC(10,2)`| `NOT NULL CHECK (>= 0)`| Verified non-negative unit price. |
| **`total_amount`** | **`NUMERIC(12,2)`**| **`NOT NULL`** | **Derived Feature**: `quantity * unit_price`. Represents line-item revenue. |
| `invoice_timestamp`| `TIMESTAMP` | `NOT NULL` | Standardized ISO-8601 UTC timestamp. |
| **`invoice_year`** | **`SMALLINT`** | **`NOT NULL`** | **Derived Feature**: `EXTRACT(YEAR FROM invoice_timestamp)`. Enables temporal grouping. |
| **`invoice_month`** | **`SMALLINT`** | **`NOT NULL`** | **Derived Feature**: `EXTRACT(MONTH FROM invoice_timestamp)`. Used for MoM analytics. |
| **`invoice_quarter`**| **`SMALLINT`** | **`NOT NULL`** | **Derived Feature**: `EXTRACT(QUARTER FROM invoice_timestamp)`. |
| **`day_of_week`** | **`VARCHAR(10)`** | **`NOT NULL`** | **Derived Feature**: Name of the weekday (e.g., `'Monday'`). |
| **`invoice_hour`** | **`SMALLINT`** | **`NOT NULL`** | **Derived Feature**: Hour of the day ($0..23$). |
| `customer_id` | `VARCHAR(20)` | `NOT NULL` | Imputed string (`'GUEST'` if original was null). |
| `customer_type` | `VARCHAR(20)` | `NOT NULL` | Derived classification (`'Registered'` vs `'Guest'`). |
| `country` | `VARCHAR(50)` | `NOT NULL` | Title-cased country name. |
| **`is_cancellation`**| **`BOOLEAN`** | **`NOT NULL`** | **Derived Flag**: `TRUE` if `invoice_no` starts with `'C'` OR `quantity < 0`. |
| **`revenue_bucket`** | **`VARCHAR(30)`** | **`NOT NULL`** | **Derived Category**: Revenue binning (`'Low'`, `'Medium'`, `'High'`, `'Cancellation'`). |

---

## ⚡ Quick Start & Dashboard Launch Setup

1. **Clone & Navigate**:
   ```bash
   git clone <repo-url>
   cd RetailLens
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in your Neon PostgreSQL connection parameters.

5. **Run the Streamlit Dashboard**:
   ```bash
   streamlit run app/main.py
   ```

6. **Run Test Suite**:
   ```bash
   python -m unittest discover tests
   ```
