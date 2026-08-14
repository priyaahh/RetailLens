# ⚡ Phase 7 Cheat Sheet (5-Minute Scale-Out Data Engineering Revision Guide)

---

## 📐 Hybrid Compute Architecture Flow

```text
Raw File ──► Size Threshold Evaluator ──► Pandas Engine (< 100MB) OR PySpark Engine (>= 100MB) ──► Parquet Lake Zone ──► PostgreSQL Fact Table
```

---

## 🔑 Key Scale-Out Definitions

* **Single-Node Bottleneck**: Processing limitation where single-thread CPU bounds and system RAM size cap dataset scalability.
* **Catalyst Optimizer**: PySpark query optimization engine that transforms high-level DataFrame transformations into optimized physical execution plans (predicate pushdown, column pruning, projection fold).
* **Parquet Format**: Open-source columnar storage file format providing high compression (Snappy), column pruning, and partition pruning.
* **Partition Pruning**: Optimization technique where query engines bypass reading entire directories by inspecting partition folder names (`year=2010/month=12`).
* **Hybrid Compute Engine**: Architectural pattern dynamically routing processing jobs to single-node Pandas or distributed PySpark based on dataset file size.

---

## 💡 Top Milestone 1 Interview Talking Points

1. *"We identified single-node Pandas bottlenecks (RAM saturation and single-threaded CPU execution) and architected a Hybrid Compute Strategy routing files >= 100MB to PySpark while preserving Pandas for lightweight local execution."*
2. *"Our PySpark transformation layer reproduces exact business rules (null imputation, whitespace trimming, cancellation flags, TotalPrice calculation) using lazy DAG execution."*
3. *"We introduced columnar Parquet storage partitioned by year and month, enabling partition pruning and reducing I/O scan volume during query aggregation."*
