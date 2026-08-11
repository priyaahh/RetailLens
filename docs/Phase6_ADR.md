# 🏗️ Phase 6 Architectural Decision Records (ADR)

This document records the key architectural decisions for **Phase 6: Scalable Data Platform & Advanced Data Engineering**.

---

## 📌 ADR 023: Incremental Ingestion & Watermark-Based Idempotent Loading

* **Decision**: Implement `WatermarkManager` (`ingestion/watermark.py`) and anti-join deduplication in `DatabaseLoader` (`ingestion/loader.py`) to enforce watermark tracking and idempotent pipeline execution.
* **Context**: Re-running ETL jobs on historical files previously appended duplicate rows into `fact_sales`, corrupting business analytics and metrics.
* **Options Considered**:
  1. Full table refresh (`if_exists="replace"`) on every run.
  2. Blind append (`if_exists="append"`) without duplicate checking.
  3. Watermark tracking (`etl_watermarks`) combined with pre-insert natural key anti-joins and unique constraints.
* **Chosen Approach**: Watermark tracking + anti-join deduplication + unique natural key constraints.
* **Why**: Guarantees pipeline idempotency (safe re-runs after failure), isolates new incremental records, avoids full table drops, and prevents revenue duplication.
* **Trade-offs**: Requires executing a lightweight `SELECT` on key columns before appending new bulk batches.
