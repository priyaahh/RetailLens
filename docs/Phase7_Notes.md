# 📖 Phase 7: Scale-Out Data Engineering & Distributed Architecture — Master Reference Notes

This document serves as the master technical documentation for **Phase 7: Scale-Out Data Engineering & Distributed Architecture** of the **RetailLens** platform.

---

## 🏛️ Phase 7 Distributed System Architecture

```text
Raw Tabular Datasets (CSV / Excel / Parquet)
                 │
                 ▼
Storage Abstraction Layer (storage/base.py & storage/local.py)
                 │
    ┌────────────┴────────────┐
    │ ComputeRouter           │  < 100MB / Configured Limit: Single-Node Pandas Engine
    │ (ingestion/router.py)   │  >= 100MB: Distributed PySpark Engine
    └────────────┬────────────┘
                 │
        ┌────────┴────────────────────────┐
        ▼                                 ▼
Pandas Ingestion Engine         PySpark Distributed Engine
(ingestion/cleaner.py)          (ingestion/spark_transformer.py)
        │                                 │
        └────────┬────────────────────────┘
                 │
                 ▼
Parquet Data Lake Storage Layer (storage/parquet_lake.py: raw, staged, processed zones)
                 │
                 ▼
Idempotent Database Loading & Anti-Join Deduplication (ingestion/loader.py)
                 │
                 ▼
Neon Cloud PostgreSQL Analytical Warehouse (fact_sales Fact Table & Audit Metadata)
                 │
                 ▼
Orchestrated DAG Workflows & Scheduler (orchestration/dag.py & scheduler.py)
                 │
                 ▼
Streamlit Operational BI & Pipeline Monitoring Dashboard
```

---

## ⚙️ Phase 7 Milestone Accomplishments

### Milestone 1 — Scalability Architecture Assessment
* Identified single-node Pandas bottlenecks (RAM saturation, single-thread CPU bounds) and defined decision matrix for Pandas vs PySpark.

### Milestone 2 — PySpark Integration (`ingestion/spark_transformer.py`)
* Created `SparkDataTransformer` executing distributed PySpark transformations with Catalyst DAG query optimization and graceful fallback when PySpark is absent.

### Milestone 3 — Hybrid Compute Router (`ingestion/compute_router.py`)
* Implemented `ComputeRouter` dynamically selecting between Pandas and PySpark based on dataset file size (`SPARK_THRESHOLD_MB=100`) and `PROCESSING_ENGINE` settings.

### Milestone 4 — Parquet Data Lake Layer (`storage/parquet_lake.py`)
* Built raw, staged, and processed data lake storage zones using Snappy-compressed Parquet files partitioned temporally by `year=YYYY/month=MM`.

### Milestone 5 — Data Lake Storage Abstraction (`storage/base.py` & `storage/local.py`)
* Architected `StorageBackend` interface with `LocalStorageBackend` implementation compatible with cloud S3/GCS object storage.

### Milestone 6 — Analytical Warehouse Architecture
* Formulated 3-tier Data Lakehouse architecture separating operational PostgreSQL, object storage lake zones, and MPP analytical data warehouses (Snowflake/BigQuery).

### Milestones 7, 8 & 9 — DAG Orchestration, Retries & Scheduling (`orchestration/`)
* Created `PipelineDAG`, `OrchestratedPipelineWorkflow`, and `PipelineScheduler` managing task dependencies, exponential backoff retries, fail-fast error handling, and concurrency locking.

### Milestones 10 & 11 — Distributed Quality & Monitoring Integration
* Extended `DataQualityMonitor` and `app/pages/pipeline_monitor.py` to display compute engine indicators (`Pandas` vs `PySpark`) and hybrid execution throughput.

### Milestone 12 — Performance Benchmarking (`ingestion/benchmark.py` & `docs/Phase7_Benchmarks.md`)
* Recorded empirical execution benchmarks proving PySpark throughput scaling for big data datasets while confirming low latency for Pandas on small files.
