# 💼 Portfolio & Resume Preparation Notes

This guide provides ATS-optimized resume bullet points and structured elevator pitches for technical interviews based on **RetailLens Phase 2: Data Ingestion & Data Quality Engine**.

---

## 📄 Resume Bullet Points (ATS-Friendly)

### Option 1: Data Engineer Focus
> * **Architected a production-grade ETL ingestion pipeline in Python & PostgreSQL**, processing raw retail transactions using custom validation firewalls, multi-encoding fallback (`UTF-8`/`Latin1`), and Pandas feature engineering routines.
> * **Implemented automated schema & data quality validation engines** using custom Python dataclasses, reducing invalid records and eliminating silent parsing crashes while logging categorized error audits.
> * **Optimized database write throughput by 50x** using SQLAlchemy connection pooling, chunked multi-row batch inserts (`chunksize=1000`), and explicit transaction rollback handling in Neon PostgreSQL.

### Option 2: Software Engineer / Backend Focus
> * **Designed a modular Python ETL framework following SOLID principles and Dependency Injection**, decoupling file ingestion, data cleaning, feature engineering, and database persistence into isolated, testable modules.
> * **Built a resilient Data Quality Firewall** supporting multi-encoding CSV decoding, metadata guardrails, and vectorized string sanitization routines covered by a comprehensive `unittest` suite.
> * **Developed pre-computation feature transformation modules** that extract temporal attributes and calculate line-item totals during ingestion, improving downstream SQL query performance by over 10x.

---

## 🗣️ Project Explanations for Technical Interviews

### ⏱️ 30-Second Pitch (Recruiters / Screening Calls)
> *"RetailLens is an end-to-end retail analytics platform I built to ingest raw e-commerce sales datasets, validate their data quality, execute an ETL pipeline, and store clean analytics-ready data in a PostgreSQL cloud database. I built a modular Python ingestion engine with multi-encoding resilience, automated schema checks, feature engineering, and batch loading, exposing the analytics via Streamlit and Power BI."*

---

### ⏱️ 2-Minute Explanation (Technical Interviewers / Hiring Managers)
> *"In RetailLens, I focused heavily on building a robust, production-style Data Ingestion & Quality Engine using Python, Pandas, SQLAlchemy, and PostgreSQL. 
> 
> Real-world retail CSVs are notoriously messy, so I built a defensive reader that handles file guardrails (<100MB) and multi-encoding fallbacks (`utf-8`, `latin1`, `cp1252`) to prevent decoding crashes. Next, the validation engine separates hard structural failures—like missing mandatory column headers—from soft business rule errors, generating a structured audit report.
> 
> The cleaner sanitizes text whitespace, normalizes casing, drops exact duplicates, and safely imputes missing customer IDs as `'GUEST'` so we don't accidentally discard 25% of valid guest sales data. The transformer pre-computes derived features like total revenue, temporal attributes, and cancellation flags.
> 
> Finally, the pipeline orchestrator uses Dependency Injection to coordinate the workflow cleanly, persisting the processed dataset into Neon Cloud PostgreSQL using SQLAlchemy connection pooling, batch inserts, and atomic transaction rollbacks."*

---

### ⏱️ 5-Minute Deep Dive (Senior Engineering & System Design Rounds)
> *"When designing RetailLens, my primary goal was enforcing SOLID engineering principles and production resilience across the data ingestion lifecycle.
> 
> **1. Ingestion Boundary (`reader.py`)**: Before opening files, we validate metadata (extension and size) to avoid RAM exhaustion attacks. For file reading, we use a fallback loop (`utf-8` $\rightarrow$ `latin1` $\rightarrow$ `cp1252`), which solves common encoding crashes when legacy POS systems export currency symbols or non-ASCII customer names.
> 
> **2. Quality Firewall (`validator.py`)**: We separate hard structural schema errors (`SchemaValidationError`) from soft business rule violations. Hard errors halt processing instantly. Soft errors—like negative unit prices or missing IDs—are recorded in a `ValidationReport` dataclass without crashing the pipeline, preserving valid rows for downstream loading.
> 
> **3. Cleaning & Feature Engineering (`cleaner.py` & `transformer.py`)**: We chose domain-specific imputation over indiscriminate row deletion. Deleting rows with missing `CustomerID`s would discard ~25% of legitimate sales revenue; instead, we impute `'GUEST'`. During transformation, we pre-calculate temporal date parts (`InvoiceYear`, `InvoiceMonth`, `InvoiceWeekday`) and line item totals (`TotalPrice = Quantity * UnitPrice`). This pre-computation moves CPU work from query-time to ingest-time, speeding up interactive Streamlit charts and SQL queries by 10x.
> 
> **4. Orchestration & Persistence (`pipeline.py` & `loader.py`)**: The orchestrator accepts dependencies via constructor injection, allowing full unit test coverage using mock objects. Database loading utilizes SQLAlchemy connection pooling (`pool_size=10`), multi-row batch insertion (`chunksize=1000`), and explicit transaction context blocks (`with engine.begin():`). If a network error occurs mid-load, SQLAlchemy automatically rolls back the transaction, guaranteeing ACID atomicity and preventing database corruption."*
