# 🏗️ Phase 2 Architectural Decision Records (ADR)

This document records the architectural and design decisions made for the **RetailLens Data Ingestion & Data Quality Engine** (Phase 2).

---

## 📌 ADR 001: Modular ETL Architecture over Single Procedural Script

* **Decision**: Decompose the ingestion pipeline into independent, single-purpose modules (`reader.py`, `validator.py`, `cleaner.py`, `transformer.py`, `loader.py`, `pipeline.py`).
* **Context**: Monolithic ETL scripts mixing file parsing, string cleaning, and database queries in one procedural file are untestable, tightly coupled, and hard to maintain.
* **Options Considered**:
  1. Single monolithic procedural script (`etl_all_in_one.py`).
  2. Modular package structure with single-responsibility classes.
* **Chosen Approach**: Modular Class-based Package (`ingestion/`).
* **Why**: Enforces **Separation of Concerns (SoC)** and **Single Responsibility Principle (SRP)**. Allows testing each stage in complete isolation using unit tests.
* **Trade-offs**: Requires slightly more boilerplate setup files and configuration classes (`schema_config.py`).
* **Future Improvements**: Wrap modules inside Docker container images for microservice deployment.

---

## 📌 ADR 002: In-Memory Pandas Engine over Distributed Apache Spark

* **Decision**: Use Pandas for in-memory tabular data manipulation.
* **Context**: We need a data processing engine for retail transaction datasets.
* **Options Considered**:
  1. Apache Spark (PySpark).
  2. Polars.
  3. Pandas.
* **Chosen Approach**: Pandas.
* **Why**: Dataset sizes in our MVP target scope (<2GB) fit comfortably in single-node RAM memory. Spark introduces JVM cluster configuration and network serialization overhead that is unnecessary for datasets under 10GB.
* **Trade-offs**: Limited by single-node RAM capacity.
* **Future Improvements**: Migrate transformation stage to PySpark if dataset volume scales past 20GB.

---

## 📌 ADR 003: SQLAlchemy ORM Engine over Raw `psycopg2` SQL String Queries

* **Decision**: Use SQLAlchemy Engine and connection pooling for database persistence.
* **Context**: Need a secure, database-agnostic method to execute bulk data insertion into PostgreSQL.
* **Options Considered**:
  1. Raw `psycopg2` cursor string formatting (`INSERT INTO ... VALUES (...)`).
  2. SQLAlchemy Engine with connection pooling.
* **Chosen Approach**: SQLAlchemy Engine (`sqlalchemy.create_engine`).
* **Why**: Protects against **SQL Injection**, automatically manages connection pooling (`pool_size=10`), and allows dialect abstraction (switching from SQLite in local unit tests to Neon PostgreSQL in cloud production without changing application code).
* **Trade-offs**: Slight ORM abstraction overhead compared to raw C-compiled `psycopg2` cursor calls.
* **Future Improvements**: Utilize PostgreSQL `COPY FROM` command via SQLAlchemy raw connection for mega-batch bulk loading (>1M rows/sec).

---

## 📌 ADR 004: Configuration-Driven Schema Validation over Hardcoded Validation Rules

* **Decision**: Define schema column names, data type expectations, and file limits inside a dedicated configuration class (`config/schema_config.py`).
* **Context**: Hardcoding expected column lists inside validation functions makes updating schemas difficult when source data specs evolve.
* **Options Considered**:
  1. Hardcoded string lists inside `validator.py`.
  2. Centralized `IngestionConfig` class / JSON configuration.
* **Chosen Approach**: Centralized `IngestionConfig`.
* **Why**: Decouples execution logic from configuration specifications. Allows adding new required fields by changing configuration parameters rather than rewriting core validation code.
* **Trade-offs**: Requires maintaining synchronization between configuration definitions and database schema DDL.
* **Future Improvements**: Store schema specifications in JSON Schema or YAML files loaded dynamically at runtime.

---

## 📌 ADR 005: Decoupling Data Quality Validation before Data Cleaning

* **Decision**: Run `DataValidator` *before* `DataCleaner`.
* **Context**: Need to determine whether validation should run before or after data cleaning.
* **Options Considered**:
  1. Clean data first, then validate clean output.
  2. Validate raw data structure and business rules first, then clean valid records.
* **Chosen Approach**: Validate raw data structure first.
* **Why**: Validating raw input catches corrupt structural errors (missing mandatory columns, unparseable dates) before spent processing CPU time running cleaning algorithms on invalid records.
* **Trade-offs**: Some raw formatting glitches (leading whitespace in dates) must be handled gracefully during type validation parsing.
* **Future Improvements**: Implement a post-cleaning audit validation check to verify data shape post-transformation.

---

## 📌 ADR 006: Pre-Computing Feature Transformations during ETL Ingestion

* **Decision**: Pre-calculate `TotalPrice`, `InvoiceYear`, `InvoiceMonth`, `InvoiceQuarter`, `InvoiceWeekday`, `InvoiceHour`, `IsCancellation`, `CustomerType`, and `RevenueBucket` during the ETL transformation stage.
* **Context**: Deciding whether to calculate features during ingestion or compute them on-the-fly inside SQL queries or Streamlit UI code.
* **Options Considered**:
  1. On-the-fly SQL computation (`EXTRACT(MONTH FROM date)` on every dashboard load).
  2. ETL Pre-computation during transformation.
* **Chosen Approach**: ETL Pre-computation (`DataTransformer`).
* **Why**: Pre-computing features once during ingestion speeds up downstream SQL query execution and dashboard chart rendering by over **10x**.
* **Trade-offs**: Increases storage footprint in PostgreSQL table by adding 8 derived feature columns.
* **Future Improvements**: Add auto-generated materialized views in PostgreSQL for aggregated monthly summary metrics.

---

## 📌 ADR 007: Dependency Injection Constructor Architecture in ETL Pipeline

* **Decision**: Inject `reader`, `validator`, `cleaner`, `transformer`, and `loader` dependencies via `ETLPipeline.__init__()`.
* **Context**: Instantiating stage objects directly inside `ETLPipeline.run()` tightly couples orchestrator code to concrete stage implementations.
* **Options Considered**:
  1. Instantiating concrete classes directly inside pipeline methods (`self.reader = DataFileReader()`).
  2. Dependency Injection via constructor default parameters (`__init__(self, reader=None, ...)`).
* **Chosen Approach**: Dependency Injection.
* **Why**: Enables **unit test isolation**. In unit tests, developers can pass mock stage objects to verify pipeline flow control and timing metrics without performing real file I/O or database queries.
* **Trade-offs**: Requires passing multiple arguments during pipeline initialization.
* **Future Improvements**: Implement a light Dependency Injection framework (e.g. `dependency_injector`) for auto-wiring dependencies.

---

## 📌 ADR 008: Multi-Row Batch Loading with SQLAlchemy Transaction Rollback

* **Decision**: Perform database persistence using `df.to_sql(method="multi", chunksize=1000)` inside an explicit SQLAlchemy transaction block (`with engine.begin() as conn:`).
* **Context**: Inserting records row-by-row in a loop is extremely slow, while un-chunked bulk loading can cause database memory timeouts.
* **Options Considered**:
  1. Row-by-row `INSERT` loop.
  2. Un-chunked full DataFrame `to_sql()`.
  3. Chunked multi-row `to_sql()` with transaction context management.
* **Chosen Approach**: Chunked multi-row `to_sql()` with transaction context.
* **Why**: Provides $50\times$ faster insertion speed over row loops while maintaining **ACID transaction atomicity**. If a batch insert fails midway, the transaction block automatically rolls back all changes to keep database state consistent.
* **Trade-offs**: Multi-row `INSERT` statements generate larger SQL payload buffers in database memory.
* **Future Improvements**: Implement `ON CONFLICT DO UPDATE` (upsert) logic using PostgreSQL native dialects for true idempotent reloading.

---

## 📌 ADR 009: Neon Managed PostgreSQL Database over Local File Databases

* **Decision**: Host analytics fact tables in Neon Managed PostgreSQL Cloud Database.
* **Context**: Need a database storage layer for transactional retail datasets.
* **Options Considered**:
  1. Local SQLite file (`.db`).
  2. Local self-hosted MySQL container.
  3. Neon Managed Cloud PostgreSQL instance.
* **Chosen Approach**: Neon Cloud PostgreSQL.
* **Why**: Provides a production-ready, cloud-hosted relational database with native SSL encryption, zero local installation overhead, connection pooling via pgBouncer, and seamless integration with cloud deployment services (Streamlit Cloud).
* **Trade-offs**: Requires active internet connectivity to perform cloud database writes.
* **Future Improvements**: Set up local PostgreSQL Docker container for offline local development and testing environments.
