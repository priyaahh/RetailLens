# 🏗️ Phase 6 Architectural Decision Records (ADR)

This document records the key architectural decisions for **Phase 6: Production Data Engineering & Pipeline Orchestration**.

---

## 📌 ADR 023: Incremental Ingestion & Watermark-Based Idempotent Loading

* **Decision**: Implement `WatermarkManager` (`ingestion/watermark.py`) and anti-join deduplication in `DatabaseLoader` (`ingestion/loader.py`).
* **Context**: Re-running ETL jobs on historical files previously appended duplicate rows into `fact_sales`.
* **Chosen Approach**: Watermark tracking + anti-join deduplication + unique natural key constraints.
* **Why**: Guarantees pipeline idempotency (safe re-runs after failure), isolates new incremental records, and avoids full table drops.

---

## 📌 ADR 024: Centralized Pipeline Execution Run Tracking (`pipeline_runs`)

* **Decision**: Implement `PipelineRunTracker` (`ingestion/tracker.py`) writing execution audit records to `pipeline_runs`.
* **Context**: Production data platforms require centralized auditability to track execution status, row counts, run duration, and error tracebacks.
* **Chosen Approach**: Decoupled `PipelineRunTracker` class executing parameterized SQL inserts and updates.
* **Why**: Isolates tracking logic from core transformation stages, providing clean auditability without code clutter.

---

## 📌 ADR 025: Data Lineage Provenance Metadata (`data_lineage`)

* **Decision**: Implement `DataLineageTracker` (`ingestion/lineage.py`) recording source-to-target mappings linked to `run_id`.
* **Context**: Enterprise data governance requires answering where target records originated and which pipeline execution created them.
* **Chosen Approach**: Linked `data_lineage` metadata table with source file, SHA-256 hash, row counts, and transformation version.
* **Why**: Enables full data provenance tracing and audit compliance.

---

## 📌 ADR 026: Operational Pipeline Monitoring Service & UI Dashboard

* **Decision**: Build `PipelineMonitoringService` (`analytics/pipeline_service.py`) and Streamlit page `app/pages/pipeline_monitor.py`.
* **Context**: Data engineers and operators require visual dashboard visibility into pipeline run health, failure rates, and quality scores.
* **Chosen Approach**: Layered architecture (`UI` -> `PipelineMonitoringService` -> `PipelineMonitoringRepository` -> `SQL Views`).
* **Why**: Decouples UI rendering from database access, maintaining strict Separation of Concerns.
