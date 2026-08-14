# 🎯 Master Technical Interview Q&A Bank (Phases 1–6)

This document contains a production-grade interview question bank derived from **Phases 1, 2, 3, 4, 5 & 6**. Use this guide to prepare for technical interview rounds across Data Engineering, Software Engineering, Backend Development, SQL, System Design, DevOps, and Business Intelligence.

---

## 🛠️ 1. Software Engineering & Architecture

### Q1: What is modular architecture, and how is it implemented in RetailLens?
**Model Answer**:
Modular architecture is a design pattern where an application is decomposed into independent, self-contained modules—each responsible for a single business capability. In RetailLens, we separate concerns across distinct directories: `ingestion/` handles data reading and file parsing, `database/` manages database connections and queries, `analytics/` processes metric calculations and ML models, and `app/` controls the UI. This ensures high cohesion within modules and loose coupling between modules, making the system testable and easy to maintain.

---

## 🚀 6. Scalable Data Platform, Pipeline Run Tracking & Data Lineage (Phase 6)

### Q49: What is the difference between a Full Refresh and an Incremental Load in ETL pipelines?
* **Strong Answer**: A **Full Refresh** wipes out target tables or reads all historical records on every execution. An **Incremental Load** identifies and processes only newly created, modified, or appended records since the last processed watermark timestamp (`MAX(invoice_timestamp)`), drastically reducing CPU, network I/O, and execution duration as datasets scale to millions of rows.
* **Keywords**: `Full Refresh vs Incremental Load`, `High-Watermark`, `CPU/Network Optimization`.

### Q50: What is pipeline Idempotency, and why is it essential for production data engineering?
* **Strong Answer**: An ETL pipeline is **idempotent** if executing it multiple times on the same input dataset produces the exact same final database state as executing it once. Idempotency ensures that re-running failed jobs or re-ingesting daily files does not insert duplicate rows or corrupt aggregated revenue metrics.
* **Keywords**: `Idempotency`, `Safe Retries`, `Anti-Join Deduplication`, `Data Integrity`.

### Q51: How do you implement Watermark Tracking in Python and PostgreSQL?
* **Strong Answer**: We store high-watermark timestamps and SHA-256 file digests in a dedicated audit table (`etl_watermarks`). Before extraction, `WatermarkManager` queries `MAX(invoice_timestamp)` from `fact_sales`. Rows with `invoice_timestamp <= watermark_ts` are filtered out before transformation, and the new watermark is recorded atomically upon load completion.
* **Keywords**: `Watermark Tracking`, `SHA-256 File Hash`, `etl_watermarks`, `High-Watermark Bound`.

### Q52: What is the difference between Exactly-Once and At-Least-Once processing semantics?
* **Strong Answer**: **At-Least-Once** guarantees every record is processed, but retries without deduplication can cause duplicates. **Exactly-Once** combines idempotent deduplication, unique natural key constraints, and atomic SQL transactions (`with engine.begin():`) to guarantee every record alters the database state precisely once.
* **Keywords**: `Exactly-Once`, `At-Least-Once`, `Deduplication`, `Atomic Transactions`.

### Q53: What is Pipeline Run Tracking, and how is it implemented in RetailLens?
* **Strong Answer**: Pipeline Run Tracking records audit execution metadata for every ETL run. In RetailLens, `PipelineRunTracker` (`ingestion/tracker.py`) inserts a `RUNNING` record in `pipeline_runs` upon job start, capturing `run_id` (UUID), file path, SHA-256 hash, start time, row count breakdowns (`rows_read`, `rows_valid`, `rows_invalid`, `rows_inserted`, `rows_skipped`), duration, and final status (`SUCCESS`, `FAILED`, `PARTIAL`, `SKIPPED`).
* **Keywords**: `PipelineRunTracker`, `pipeline_runs Table`, `Audit Trail`, `Run Lifecycle`.

### Q54: What is Data Lineage, and why is it crucial for data governance?
* **Strong Answer**: Data Lineage tracks the lifecycle and origin of data from source files to destination database tables. `DataLineageTracker` (`ingestion/lineage.py`) records source file paths, SHA-256 hashes, source row counts, target tables (`fact_sales`), target row counts, and transformation version codes linked to `run_id` in `data_lineage`. It enables data engineers to answer: *"Which pipeline run created these records?"* and *"Where did this database record come from?"*.
* **Keywords**: `Data Lineage`, `Data Provenance`, `Transformation Versioning`, `Audit Compliance`.

### Q55: How do you ensure pipeline failure recovery without leaving orphan RUNNING locks or corrupting database tables?
* **Strong Answer**: We implement atomic transaction management and exception interception in `ETLPipeline.run()`. When an unhandled exception occurs, the catch block calls `PipelineRunTracker.fail_run()`, recording `status = 'FAILED'` and the exact error traceback in `pipeline_runs`. Furthermore, database loads use SQLAlchemy transaction blocks (`with engine.begin():`), ensuring partial batch writes automatically roll back on failure.
* **Keywords**: `Failure Recovery`, `Atomic Rollback`, `Fail-Fast`, `Exception Interception`.

### Q56: How does Data Quality Monitoring differ from static input schema validation?
* **Strong Answer**: Static input validation checks column headers and data types before processing. Data Quality Monitoring (`DataQualityMonitor` in `ingestion/quality_monitor.py`) evaluates quantitative quality scores (`valid_rows / total_rows * 100`), processing speed (`records_per_second`), duplicate skip rates, null imputation counts, and evaluates warning/critical alert thresholds after pipeline execution.
* **Keywords**: `Data Quality Monitoring`, `Quality Score %`, `Throughput Metrics`, `Threshold Badges`.

### Q57: How is the Operational Monitoring Dashboard structured in RetailLens?
* **Strong Answer**: Following our layered architecture, `app/pages/pipeline_monitor.py` consumes `PipelineMonitoringService`, which queries `PipelineMonitoringRepository` against PostgreSQL views (`view_latest_pipeline_runs`, `view_failed_pipeline_runs`, `view_pipeline_daily_summary`, `view_data_quality_summary`). It displays overall system health badges, latest run details, recent run audit trails, data quality summaries, and data lineage provenance.
* **Keywords**: `PipelineMonitoringService`, `Streamlit Monitor Dashboard`, `Operational Views`, `Health Badges`.
