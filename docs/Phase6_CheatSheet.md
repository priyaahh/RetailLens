# ⚡ Phase 6 Cheat Sheet (5-Minute Production Pipeline Revision Guide)

---

## 📐 End-to-End Pipeline Audit Flow

```text
Input File ──► SHA-256 Hash ──► PipelineRunTracker (start_run) ──► Validation & Cleaning ──► Anti-Join Load ──► DataLineageTracker & QualityMonitor ──► complete_run / fail_run
```

---

## 🔑 Key Definitions & Architecture Terms

* **Incremental Load**: Processing only new or modified records created since the last high watermark (`MAX(invoice_timestamp)`).
* **Pipeline Run Tracking**: Audit mechanism logging execution status (`RUNNING`, `SUCCESS`, `FAILED`), row counts, and duration in `pipeline_runs`.
* **Data Lineage**: Provenance metadata recording source file path, SHA-256 content hash, transformation version, and target table for audit governance.
* **Idempotency**: Operation property ensuring repeated execution yields identical final database states without duplicate records.
* **Data Quality Score**: Percentage of valid, non-rejected rows (`valid_rows / total_rows * 100`) calculated per execution run.
* **SQL Filter Pushdown**: Executing aggregations (`SUM`, `COUNT`, `AVG`) directly inside PostgreSQL using indexes to return scalar metrics.

---

## 💡 Top Phase 6 Interview Talking Points

1. *"We achieved pipeline idempotency by combining SHA-256 file hash tracking in `etl_watermarks` with natural key anti-joins in `DatabaseLoader`."*
2. *"Our audit engine (`PipelineRunTracker`) records execution run status (`RUNNING`, `SUCCESS`, `FAILED`), row breakdown statistics, and execution duration in `pipeline_runs`."*
3. *"We established data provenance using `DataLineageTracker`, mapping every target record batch back to its raw source file, SHA-256 hash, and transformation version."*
4. *"We built an operational monitoring service (`PipelineMonitoringService`) and Streamlit dashboard tab displaying system health badges, failure alerts, and quality scores."*
