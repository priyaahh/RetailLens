# 📖 Phase 6: Scalable Data Platform & Advanced Data Engineering — Reference Notes

This document serves as the master technical documentation for **Phase 6: Scalable Data Platform & Advanced Data Engineering** of the **RetailLens** platform.

---

## 🏛️ Phase 6 System Architecture

```text
Raw CSV / Excel Dataset
         │
         ▼
Watermark Inspection & SHA-256 Hash Verification (ingestion/watermark.py)
         │
         ▼
Phase 2/6 ETL Pipeline (Reader ──► Validator ──► Cleaner ──► Transformer ──► Loader)
         │
         ▼
Idempotent Deduplication & Staging (loader.py)
         │
         ▼
Neon Cloud PostgreSQL (fact_sales Fact Table & etl_watermarks Audit Table)
         │
         ▼
Phase 3/4 Analytics Engine (Repository ──► KPI Engine ──► Insight Engine ──► Service)
         │
         ▼
Streamlit BI Dashboard & Observability Layer
```

---

## ⚙️ Milestone 1 — Incremental ETL & Idempotent Data Loading

### 1. Problem Solved
Prior to Milestone 1, running the ETL pipeline on an input dataset loaded all rows into PostgreSQL without checking if records or files were previously ingested. Re-running the pipeline inserted duplicate rows into `fact_sales`, corrupting revenue and order count aggregations.

### 2. Architecture & Solution
* **`WatermarkManager` (`ingestion/watermark.py`)**: Computes SHA-256 hashes of incoming data files and stores high-watermark timestamps (`MAX(invoice_timestamp)`) in `etl_watermarks`.
* **High-Watermark Incremental Filter**: Filters out historical records (`invoice_timestamp <= watermark_ts`) before validation and transformation stages.
* **Idempotent Database Loading (`ingestion/loader.py`)**: `DatabaseLoader` performs left anti-joins against existing natural business keys `(invoice_no, stock_code, invoice_timestamp)` before appending, guaranteeing that re-executing pipeline jobs results in zero duplicate rows.
* **Unique Constraints (`database/schema.sql`)**: Enforces `CONSTRAINT uq_fact_sales_natural_key UNIQUE (invoice_no, stock_code, invoice_timestamp)`.
