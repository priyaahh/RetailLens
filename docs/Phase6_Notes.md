# 📖 Phase 6: Production Data Engineering & Pipeline Orchestration — Master Engineering Reference

This document serves as the master technical documentation for **Phase 6: Production Data Engineering & Pipeline Orchestration** of the **RetailLens** platform.

---

## 🏛️ Phase 6 System Architecture

```text
CSV / Excel Tabular Dataset
           │
           ▼
Stage 0: SHA-256 Hash & High Watermark Inspection (ingestion/watermark.py)
           │
           ▼
Stage 1: Extraction & Incremental Watermark Filtering (ingestion/reader.py & watermark.py)
           │
           ▼
Stage 2: Schema & Data Quality Validation (ingestion/validator.py)
           │
           ▼
Stage 3: Data Cleaning & Null Imputation (ingestion/cleaner.py)
           │
           ▼
Stage 4: Feature Transformation & Temporal Engineering (ingestion/transformer.py)
           │
           ▼
Stage 5: Idempotent Anti-Join Database Loading (ingestion/loader.py)
           │
           ├──► Neon PostgreSQL (fact_sales Fact Table & etl_watermarks)
           │
           ├──► Pipeline Run Tracking (ingestion/tracker.py -> pipeline_runs Table)
           │
           ├──► Data Lineage Provenance (ingestion/lineage.py -> data_lineage Table)
           │
           └──► Data Quality Monitoring (ingestion/quality_monitor.py -> DataQualitySummary)
                     │
                     ▼
Operational Monitoring Service Layer (analytics/pipeline_service.py & pipeline_repository.py)
                     │
                     ▼
Streamlit Pipeline Monitoring Dashboard (app/pages/pipeline_monitor.py)
```

---

## ⚙️ Phase 6 Milestone Accomplishments

### Milestone 1 — Incremental ETL & Idempotent Loading
* **`WatermarkManager` (`ingestion/watermark.py`)**: Computes SHA-256 file hashes to detect duplicate file re-ingestion and retrieves high-watermark bounds (`MAX(invoice_timestamp)`).
* **Anti-Join Deduplication (`ingestion/loader.py`)**: `DatabaseLoader` performs left anti-joins against existing natural keys `(invoice_no, stock_code, invoice_timestamp)` before appending, preventing duplicate row insertion on re-runs.

### Milestone 2 — Pipeline Run Tracking (`ingestion/tracker.py`)
* **`PipelineRunTracker`**: Manages execution audit records in the `pipeline_runs` database table.
* **Run Status Lifecycle**: Tracks execution status (`RUNNING`, `SUCCESS`, `FAILED`, `PARTIAL`, `SKIPPED`), row metrics (`rows_read`, `rows_valid`, `rows_invalid`, `rows_transformed`, `rows_inserted`, `rows_skipped`), execution duration, and error messages.

### Milestone 3 — Data Lineage Provenance (`ingestion/lineage.py`)
* **`DataLineageTracker`**: Records source-to-target data lineage metadata linked to `run_id` in `data_lineage` table, linking raw files to target PostgreSQL tables (`fact_sales`).

### Milestone 4 — Failure Recovery & Transaction Safety
* **Exception Interception**: Intercepts stage errors, ensuring failed runs are logged as `FAILED` in `pipeline_runs` without leaving orphan `RUNNING` locks.
* **Exponential Backoff**: Reuses `database/retry.py` for transient database connection retries while failing fast on permanent schema errors.

### Milestone 5 & 7 — Data Quality Monitoring & Metrics (`ingestion/quality_monitor.py`)
* **`DataQualityMonitor` & `DataQualitySummary`**: Computes automated data quality scores (`valid_rows / total_rows * 100`), processing speed (`records_per_second`), duplicate skip rates, and evaluates warning/critical thresholds.

### Milestone 6 — Pipeline Observability & Stage Logging
* **Structured Stage Logs**: Emits standardized stage logs (`[STAGE: READ]`, `[STAGE: VALIDATE]`, `[STAGE: CLEAN]`, `[STAGE: TRANSFORM]`, `[STAGE: LOAD]`, `[STAGE: COMPLETE]`) with `SensitiveDataFilter` secret masking.

### Milestone 8 — Operational Database Views
* **Database Views (`database/schema.sql`)**:
  * `view_latest_pipeline_runs`
  * `view_failed_pipeline_runs`
  * `view_pipeline_daily_summary`
  * `view_data_quality_summary`

### Milestone 9 & 10 — Monitoring Service & Streamlit Dashboard (`analytics/pipeline_service.py` & `app/pages/pipeline_monitor.py`)
* **`PipelineMonitoringService` & UI Page**: Exposes high-level monitoring APIs and renders a dedicated Streamlit dashboard tab displaying system health badges, latest run details, recent run audit tables, quality scores, and data lineage provenance.
