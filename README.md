# 🚀 RetailLens – End-to-End Retail Analytics Platform

[![RetailLens CI Pipeline](https://github.com/retail-analytics/RetailLens/actions/workflows/ci.yml/badge.svg)](https://github.com/retail-analytics/RetailLens/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15%2B-blue.svg)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/docker-ready-cyan.svg)](https://docker.com)

RetailLens is an enterprise-grade retail analytics platform built with Python, PostgreSQL, Streamlit, Docker, and GitHub Actions. It ingests raw transaction datasets, executes automated schema and data quality validation, runs a modular ETL pipeline, stores structured fact tables in a cloud PostgreSQL database, and exposes an advanced SQL analytics engine, automated business insights, and an interactive Streamlit BI web application.

---

## ✨ System Highlights (Phases 1–5 Completed)

* 🔄 **End-to-End Modular ETL Pipeline**: Modular Python orchestrator (`ETLPipeline`) coordinating extraction, validation, cleaning, feature engineering, and staging.
* 🛡️ **Data Quality & Security Firewall**: Automated schema enforcement, multi-encoding fallback (`utf-8` $\rightarrow$ `cp1252`), 100MB file boundaries, and path traversal prevention.
* 🐘 **Cloud PostgreSQL Database Layer**: Managed relational database (Neon PostgreSQL) hosting dimensional fact models (`fact_sales`, `dim_customer`, `dim_product`) with B-Tree indexes.
* 📊 **Master SQL Analytics Catalog**: 25 business and advanced SQL queries utilizing aggregations, CTEs, window functions (`DENSE_RANK()`, `LAG()`), and date analytics.
* 📈 **Python Analytics Engine**: `AnalyticsRepository`, `KPIEngine`, `InsightEngine`, and `AnalyticsService` executing SQL pushdown aggregations with `NULLIF` zero-division protection.
* 💡 **Automated Business Insights**: Anomaly detection engine evaluating metrics against configurable thresholds to emit structured `Insight` objects with severity badges and recommendations.
* 💻 **Interactive Streamlit Dashboard**: 6-page BI web application featuring responsive KPI cards, dynamic Plotly charts, sidebar filters, and two-tier caching (`@st.cache_data`, `@st.cache_resource`).
* ⚙️ **Centralized Configuration & Security**: `AppConfig` validating environment profiles (`development`, `production`), masking credentials in logs via `SensitiveDataFilter`.
* 🛡️ **Reliability & Resilience**: Exponential backoff retries (`execute_with_retry`) for transient database failures with fail-fast validation.
* 🤖 **CI/CD & Docker Containerization**: GitHub Actions CI workflow (`ci.yml`) and multi-stage production `Dockerfile` with HTTP healthchecks.

---

## 📚 Documentation & Engineering Notes

Detailed technical notes, architectural decision records (ADR), and technical interview preparation materials are organized in the [`docs/`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs) directory:

* 📄 [**Phase 1 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase1_Notes.md) – Project foundation & initial architecture.
* 📄 [**Phase 2 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase2_Notes.md) – Data Ingestion, Data Quality Validation, Cleaning, and Staging.
* 📄 [**Phase 3 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase3_Notes.md) – PostgreSQL Relational Schema, Master SQL Catalog, Window Functions, and Indexing.
* 📄 [**Phase 4 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase4_Notes.md) – Streamlit Web App Architecture, UI Components, and Caching.
* 📄 [**Phase 5 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase5_Notes.md) – Production Hardening, Configuration, Observability, Reliability, Security, CI/CD, and Docker.
* 📄 [**Analytics & BI Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Analytics_Notes.md) – Repository Pattern, KPI Engine, and Insight Engine design.
* 📄 [**Deployment Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Deployment_Notes.md) – Local Docker execution and Streamlit Cloud setup instructions.
* 📄 [**Interview Q&A Guide**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Interview_QA.md) – Master Q&A bank with 48 interview questions across software engineering, data engineering, SQL, system design, security, CI/CD, and Docker.
* 📄 [**Production Checklist**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Production_Checklist.md) – Master 30-point production readiness evaluation.

---

## 📐 System Architecture & Network Flow

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                                CLIENT BROWSER                                    │
│  User visits https://retaillens.streamlit.app                                    │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │  HTTP/2 & WebSocket (wss:// Port 443 / 8501)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                       DOCKER CONTAINER / STREAMLIT CLOUD                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │             STREAMLIT WEB APPLICATION ROUTER (app/main.py)                 │  │
│  │  Multi-Page Router  ◄──► Sidebar Filters  ◄──► Plotly Chart Engine         │  │
│  │  Pages: Overview, Sales, Products, Customers, Insights, Operations         │  │
│  └─────────────────────────────────────┬──────────────────────────────────────┘  │
│                                        │ Internal Function Calls                 │
│                                        ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION ETL & ANALYTICS LAYER                       │  │
│  │  ETLPipeline ──► AnalyticsService ──► KPI Engine ──► Insight Engine        │  │
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

## ⚡ Quick Start Setup

### 1. Local Setup
```bash
git clone <repo-url>
cd RetailLens

python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1 | Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run Dashboard
streamlit run app/main.py

# Run Full Test Suite
python -m unittest discover tests
```

### 2. Docker Container Setup
```bash
docker build -t retaillens:latest .
docker run -d -p 8501:8501 --env-file .env retaillens:latest
```
