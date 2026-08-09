# ⚙️ Comprehensive ETL Pipeline Notes & Reference Guide

This document tracks technical implementations, architectural concepts, and production patterns across the Extract, Transform, and Load lifecycle of RetailLens.

---

## 📚 1. Core Data Engineering Concepts

### Extract (E)
The process of retrieving raw data from underlying source systems (e.g., transactional SQL databases, REST APIs, microservice event streams, or tabular CSV/Excel files). In RetailLens, `DataFileReader` ([`ingestion/reader.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/reader.py)) extracts tabular records with multi-encoding fallback.

### Transform (T)
The process of converting raw, un-sanitized data into a clean, standardized, enriched format suitable for business intelligence and analytics. In RetailLens, transformation is split across validation (`validator.py`), cleaning (`cleaner.py`), and feature engineering (`transformer.py`).

### Load (L)
The process of persisting transformed data into target storage destinations (relational databases, cloud data warehouses, or data lakes). In RetailLens, `DatabaseLoader` ([`ingestion/loader.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/loader.py)) performs chunked multi-row batch inserts into PostgreSQL.

### Data Quality & Data Quality Firewall
Data Quality defines the accuracy, completeness, consistency, and reliability of data. A **Data Quality Firewall** is an automated validation checkpoint placed at the ingestion entry point to inspect data structure and business rules *before* data reaches storage.

### Data Contracts
A formal agreement between data producers (e.g. POS software teams) and data consumers (data engineering teams) specifying schema expectations, column data types, SLA boundaries, and null tolerance thresholds. In RetailLens, `config/schema_config.py` enforces our data contract.

### Data Lineage
The end-to-end lifecycle trail tracking where data originated, how it was transformed across each pipeline stage, and where it is consumed.

### Data Profiling
The analytical practice of inspecting raw datasets to discover statistical distributions, null value frequencies, duplicate counts, and data type anomalies before building transformation rules.

### Data Governance
The overall management framework defining data ownership, privacy security compliance, data retention policies, and access controls across an organization.

---

## 🏗️ 2. Production ETL Patterns & Architecture

### Batch Processing vs. Streaming Processing
* **Batch Processing (RetailLens)**: Processing discrete, bounded datasets collected over a fixed time period (e.g., daily CSV uploads). Highly efficient for complex aggregations and bulk loading.
* **Streaming Processing (Kafka / Flink)**: Processing continuous, unbounded event feeds item-by-item in real-time ($<100$ms latency).

### Full Refresh vs. Incremental Loading
* **Full Refresh (RetailLens MVP)**: Overwriting or re-inserting the entire target database table during each pipeline run. Simple to maintain for smaller datasets.
* **Incremental Loading (CDC / Delta Load)**: Ingesting only newly created or modified records since the last execution timestamp, drastically reducing database processing load for large datasets.

### Change Data Capture (CDC)
A technology pattern (e.g., Debezium) that reads database transaction write logs (WAL in PostgreSQL) to track row insertions, updates, and deletions in real-time without querying source tables.

### Dead Letter Queues (DLQ) & Quarantine Directories
A design pattern where malformed, unparseable, or corrupt data records are isolated into a separate quarantine storage location (`data/invalid/`) for asynchronous developer inspection while allowing valid records to proceed.

### Retry Mechanisms & Circuit Breakers
Automated policies that retry transient failures (e.g., momentary cloud database network dropouts) up to $N$ times with exponential backoff before marking a pipeline run as failed.

---

## ⚡ 5-Minute Ingestion & Pipeline Revision Cheat Sheet
* **Dependency Injection in Pipelines**: Always pass stage objects (`reader`, `validator`, `cleaner`) into the orchestrator constructor so unit tests can swap real instances with mocks.
* **Fail-Fast Strategy**: Halt pipeline execution immediately on hard schema errors (`SchemaValidationError`), but allow soft business rule anomalies to pass through with audit tracking.
* **Execution Metrics**: Always track start time, end time, duration, rows read, valid rows, invalid rows, and final transformed rows in a structured `PipelineResult` object.
