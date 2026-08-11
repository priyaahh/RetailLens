# 🎯 Master Technical Interview Q&A Bank (Phases 1–6)

This document contains a production-grade interview question bank derived from **Phases 1, 2, 3, 4, 5 & 6**. Use this guide to prepare for technical interview rounds across Data Engineering, Software Engineering, Backend Development, SQL, System Design, DevOps, and Business Intelligence.

---

## 🛠️ 1. Software Engineering & Architecture

### Q1: What is modular architecture, and how is it implemented in RetailLens?
**Model Answer**:
Modular architecture is a design pattern where an application is decomposed into independent, self-contained modules—each responsible for a single business capability. In RetailLens, we separate concerns across distinct directories: `ingestion/` handles data reading and file parsing, `database/` manages database connections and queries, `analytics/` processes metric calculations and ML models, and `app/` controls the UI. This ensures high cohesion within modules and loose coupling between modules, making the system testable and easy to maintain.

---

## ⚙️ 5. Production Hardening & Configuration (Phase 5)

### Q41: How do you handle environment configuration safely across development, testing, staging, and production environments?
* **Strong Answer**: In RetailLens, we created a centralized configuration engine (`AppConfig` in `config/app_config.py`). Instead of reading loose `os.getenv()` calls across components, `AppConfig` validates configuration types and enforces profile rules (`development`, `testing`, `staging`, `production`). In `production`, `AppConfig` mandates complete database credentials (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`) and rejects default dev keys, raising `ConfigurationError` before app startup.
* **Keywords**: `Centralized Configuration`, `Environment Profiles`, `Strict Validation`, `AppConfig`.

---

## 🚀 6. Scalable Data Platform & Incremental ETL (Phase 6 Milestone 1)

### Q49: What is the difference between a Full Refresh and an Incremental Load in ETL pipelines?
* **Strong Answer**: 
  A **Full Refresh** wipes out target tables or reads all historical records on every execution, processing the entire dataset from scratch. An **Incremental Load** identifies and processes only newly created, modified, or appended records since the last processed watermark timestamp (`MAX(invoice_timestamp)`). Incremental loading drastically reduces CPU, network I/O, and runtime duration as datasets grow to millions of rows.
* **Why RetailLens does this**: `WatermarkManager` reads the high-watermark timestamp from `fact_sales` and filters out historical rows before validation and transformation.
* **Keywords**: `Full Refresh vs Incremental Load`, `High-Watermark`, `CPU/Network Optimization`.

### Q50: What is pipeline Idempotency, and why is it essential for production data engineering?
* **Strong Answer**: 
  An ETL pipeline is **idempotent** if executing it multiple times on the same input dataset produces the exact same final database state as executing it once. In production pipelines, network timeouts or server restarts can interrupt execution halfway through. Idempotency ensures that re-running failed jobs does not insert duplicate rows or corrupt aggregated metrics.
* **Why RetailLens does this**: We combine SHA-256 file hash tracking in `etl_watermarks` with anti-join deduplication on composite natural keys `(invoice_no, stock_code, invoice_timestamp)` in `DatabaseLoader`.
* **Keywords**: `Idempotency`, `Safe Retries`, `Anti-Join Deduplication`, `Data Integrity`.

### Q51: How do you implement Watermark Tracking in Python and PostgreSQL?
* **Strong Answer**: 
  We store high-watermark timestamps and SHA-256 file digests in a dedicated audit table (`etl_watermarks`). Before executing extraction, `WatermarkManager` queries `MAX(invoice_timestamp)` from `fact_sales`. During processing, rows with `invoice_timestamp <= watermark_ts` are filtered out. Upon stage 5 completion, `WatermarkManager` records the new file hash, timestamp, and row count atomically.
* **Keywords**: `Watermark Tracking`, `SHA-256 File Hash`, `etl_watermarks`, `High-Watermark Bound`.

### Q52: What is the difference between Exactly-Once and At-Least-Once processing semantics?
* **Strong Answer**: 
  **At-Least-Once** guarantees that every data record is processed at least once, but retries without deduplication may cause duplicate database entries. **Exactly-Once** combines idempotent deduplication, unique natural key constraints, and atomic SQL transactions (`with engine.begin():`) to guarantee every record alters the database state precisely once.
* **Keywords**: `Exactly-Once`, `At-Least-Once`, `Deduplication`, `Atomic Transactions`.
