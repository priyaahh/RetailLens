# 🏗️ Phase 7 Architectural Decision Records (ADR)

This document records the key architectural decisions for **Phase 7: Scale-Out Data Engineering & Distributed Architecture**.

---

## 📌 ADR 027: Hybrid Compute Strategy & Configurable PySpark Engine

* **Decision**: Implement a hybrid compute architecture combining a single-node Pandas engine for small batch files (< 100MB) with a distributed PySpark engine for large dataset processing.
* **Context**: Single-node Pandas ingestion saturates system RAM and single-thread CPU bounds when dataset size exceeds available memory.
* **Options Considered**:
  1. Pure Pandas with chunked iteration (`pd.read_csv(chunksize=10000)`).
  2. Complete rewrite to PySpark-only for all ingestion.
  3. Hybrid Compute Engine selecting Pandas vs PySpark based on dataset size and configuration flags.
* **Chosen Approach**: Hybrid Compute Engine with configurable threshold and fallback capability.
* **Why**: Preserves fast, zero-dependency local execution for unit tests and small development files while unlocking cluster-scale parallel processing for big data files.
* **Trade-offs**: Requires maintaining dual transformation routines (Pandas `DataTransformer` and PySpark `SparkDataTransformer`) under identical business rule contracts.

---

## 📌 ADR 028: Data Lakehouse & Analytical Warehouse Layering Strategy

* **Decision**: Establish a 3-tier Data Lakehouse architecture cleanly separating raw storage, staging, and analytical warehouse target zones.
* **Context**: Mixing operational OLTP databases with heavy analytical data warehousing causes connection starvation and locks transactional application threads.
* **Architecture Pattern**:
  1. **Raw / Staging Zone**: Object storage storing ingested CSV / Excel / Parquet files (`data/lake/raw/`).
  2. **Processed Data Lake Zone**: Partitioned Parquet format (`year=YYYY/month=MM`) using Snappy compression (`data/lake/processed/`).
  3. **Analytical Warehouse Layer**: Dimensional Star Schema (`fact_sales`, `dim_customer`, `dim_product`) hosted on Neon PostgreSQL or Snowflake MPP.
* **Why**: Decouples storage from compute, maximizes compression rates, and allows independent scaling of batch ingestion pipelines and BI query workloads.
