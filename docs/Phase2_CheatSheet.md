# ⚡ Phase 2 Cheat Sheet (5-Minute Interview Revision Guide)

---

## 📐 Architecture Summary

```text
┌─────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ DataFileReader  │ ──► │   DataValidator   │ ──► │    DataCleaner    │
│ (Metadata & CSV)│     │(Schema & Quality) │     │ (Nulls & Clean)   │
└─────────────────┘     └───────────────────┘     └─────────┬─────────┘
                                                            │
┌─────────────────┐     ┌───────────────────┐               │
│ DatabaseLoader  │ ◄── │  ETLPipeline Run  │ ◄─────────────┘
│(Postgres Batch) │     │  DataTransformer  │
└─────────────────┘     │ (Feature Engine)  │
                        └───────────────────┘
```

---

## 🔑 Key Concepts & Definitions (1-Line Explanations)

* **ETL (Extract, Transform, Load)**: Data engineering pipeline pattern reading raw files, cleaning/transforming them in memory, and persisting them into databases.
* **Data Quality Firewall**: Defensive validation layer inspecting data for schema, type, and business rule violations before storage.
* **ValidationReport**: Structured dataclass tracking total, valid, and invalid row counts alongside categorized error audit metrics.
* **Idempotency**: Property where re-running an ETL pipeline multiple times produces the exact same database state without duplicate records or errors.
* **ACID Properties**: Database transaction guarantees: Atomicity (all-or-nothing), Consistency, Isolation, Durability.
* **Batch Processing**: Ingesting and processing data in finite bulk chunks rather than continuous single-record streams.
* **Connection Pooling**: Reusing a pool of open database connections to avoid the network overhead of opening/closing sockets on every query.
* **Dependency Injection (DI)**: Passing dependent objects into a class constructor rather than hardcoding their instantiation internally.
* **Separation of Concerns (SoC)**: Software design pattern isolating application features into distinct single-responsibility modules.
* **OLTP vs. OLAP**: OLTP (PostgreSQL) is row-oriented for fast write transactions; OLAP (Snowflake/BigQuery) is column-oriented for petabyte analytical aggregations.

---

## 🛠️ Execution & Testing Commands

```bash
# Run complete test suite
python -m unittest discover tests

# Run specific module test
python -m unittest tests/test_pipeline.py

# Test ETL pipeline manually in Python shell
python -c "from ingestion import ETLPipeline, PipelineConfig; res = ETLPipeline(config=PipelineConfig(load_data=False)).run('data/raw/online_retail.csv'); print(res)"
```

---

## 💡 Top 5 Interview Talking Points

1. *"We built a defensive Data Quality Firewall using multi-encoding fallback (`utf-8` $\rightarrow$ `latin1` $\rightarrow$ `cp1252`) and pre-read file size checks to protect server RAM against Out-of-Memory crashes."*
2. *"We separate hard structural schema failures (`SchemaValidationError`) from soft business rule anomalies (`ValidationReport`), allowing valid rows to be processed while bad rows are audited."*
3. *"Instead of dropping rows with missing customer IDs—which would eliminate 25% of overall sales revenue data—we impute `CustomerID = 'GUEST'` to preserve total sales metrics."*
4. *"We pre-compute derived features (`TotalPrice`, `InvoiceMonth`, `InvoiceWeekday`, `RevenueBucket`) during ETL transformation, making downstream SQL queries 10x faster."*
5. *"Our database loader uses SQLAlchemy connection pooling, chunked multi-row batch inserts (`chunksize=1000`), and transaction context blocks to guarantee ACID atomicity and prevent partial load corruption."*
