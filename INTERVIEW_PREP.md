# RetailLens — 20-Minute Master Technical Interview Guide

> **Quick Context**: Keep this guide open before your interview. It summarizes everything you built, why you built it, the numbers to cite, and how to defend every engineering decision in simple, confident English.

---

## 1. The 30-Second Elevator Pitch

> *"RetailLens is an end-to-end retail analytics platform and automated ETL data pipeline that converts raw, messy e-commerce sales exports into live executive business intelligence.*
>
> *In real-world retail, daily POS exports frequently break analytics systems due to non-UTF-8 currency symbols, missing customer IDs, negative prices, and sudden file spikes. I built RetailLens to eliminate this pipeline fragility: it validates file quality at the entry gate, routes large files to Apache Spark, loads clean data into PostgreSQL 50x faster using chunked batch transactions, and serves real-time business insights on a Streamlit dashboard with sub-millisecond Redis caching."*

---

## 2. Tech Stack at a Glance

| Technology | What I Used It For | Why I Chose It Over Alternatives |
| :--- | :--- | :--- |
| **Python 3.10+** | Core pipeline, analytics service, and API logic | Rich data ecosystem, native type hinting, and rapid prototyping. |
| **Pandas** | In-memory cleaning & feature engineering (< 100MB) | Zero cluster overhead; vectorized C-compiled operations execute in milliseconds on single nodes. |
| **PySpark** | Distributed big-data transformations ($\ge$ 100MB) | Breaks large files across CPU cores/partitions, avoiding Out-of-Memory (OOM) RAM crashes. |
| **PostgreSQL (Neon)** | Analytical data warehouse hosting fact & dimension tables | Full ANSI SQL support, ACID transaction safety, CTEs, and window functions (`DENSE_RANK`, `LAG`). |
| **SQLAlchemy 2.0** | Connection pooling and bulk persistence | Reuses open TCP sockets (`pool_size=10`) and executes atomic multi-row batch inserts (`chunksize=1000`). |
| **Parquet & Snappy** | Columnar storage for long-term Data Lake archive | Compresses files by **68%** and enables partition pruning (`year/month`) for 74% faster scans. |
| **Redis** | Query result caching layer | Delivers sub-millisecond dashboard KPI responses with automatic in-memory fallback on disconnect. |
| **Streamlit & Plotly** | Interactive executive BI dashboard & charts | Pure-Python reactivity eliminates complex JavaScript build tooling and frontend state syncing. |
| **Docker (Multi-Stage)**| Containerization & production packaging | 2-stage build discards compilers from runtime, reducing final image size by **70%**. |
| **Kubernetes (K8s)** | Cloud orchestration, health probes, and autoscaling | Self-heals crashed pods via liveness probes and auto-scales from 2 to 10 pods via HPA on traffic spikes. |

---

## 3. Architecture in 6 Lines (How Data Flows)

```text
[Raw CSV / Excel] ──► [Defensive Reader] ──► [Quality Firewall] ──► [Compute Router]
                                                                          │
  ┌───────────────────────────────◄───────────────────────────────────────┘
  ▼
[Clean & Transform] ──► [Snappy Parquet Lake] ──► [PostgreSQL Batch Load] ──► [Redis + Streamlit]
```

1. **Ingest & Guardrail**: Raw exports (.csv/.xlsx) enter via `DataFileReader`, which checks file size (<100MB guardrail) and runs an automated encoding fallback loop (`utf-8` $\rightarrow$ `latin1` $\rightarrow$ `cp1252`) to prevent decoding crashes.
2. **Quality Firewall**: `DataValidator` inspects headers and business rules; structural errors abort execution immediately, while row errors (negative prices, future dates) are isolated into a `ValidationReport`.
3. **Hybrid Compute Routing**: `ComputeRouter` routes datasets $<100$MB to Pandas and $\ge100$MB to PySpark, optimizing memory and startup overhead.
4. **Sanitize & Feature Engineer**: `DataCleaner` normalizes casing and imputes missing `CustomerID` as `'GUEST'`. `DataTransformer` pre-computes `TotalPrice`, 6 temporal fields, cancellation flags, and revenue tiers.
5. **Dual Persistence**: The clean dataset is saved as Snappy Parquet partitioned by `(InvoiceYear, InvoiceMonth)` in the Data Lake, and bulk-inserted into PostgreSQL `fact_sales` in 1,000-row chunks with deduplication.
6. **Analytics & Dashboard**: `AnalyticsService` executes parameterized SQL queries, caches results in Redis (5-minute TTL), and renders interactive executive charts and operational health monitors in Streamlit.

---

## 4. 5 Key Technical Decisions & Why I Made Them

### 1. PostgreSQL instead of SQLite or MongoDB
* **Reason**: SQLite is a local file-based database that locks the entire file during writes, making concurrent dashboard queries and pipeline writes impossible. MongoDB lacks native relational joins and analytical window functions. Managed PostgreSQL provides full ANSI SQL, ACID transaction safety, and high-performance B-tree indexing on transactional foreign keys.

### 2. Hybrid Compute Router (Pandas + PySpark) instead of Spark-Only
* **Reason**: PySpark requires initializing a JVM and `SparkContext`, incurring a 1–2 second startup penalty. For a typical 2MB daily retail export, running Spark adds needless latency. Pandas processes small files instantaneously. The router uses Pandas for speed on small files and PySpark only when files exceed 100MB to avoid OOM crashes.

### 3. Imputing `CustomerID = 'GUEST'` instead of Dropping Missing Rows
* **Reason**: In e-commerce datasets, ~25% of purchases are guest checkouts without user accounts. Running a standard `df.dropna(subset=['CustomerID'])` would discard 25% of the company's real revenue! Imputing `'GUEST'` keeps gross revenue metrics 100% accurate while letting customer analytics segment registered vs. guest cohorts.

### 4. Pre-Computing Features at Ingest instead of Calculating On-the-Fly in SQL
* **Reason**: Calculating `TotalPrice = Quantity * UnitPrice` and parsing dates across 500,000+ rows every time a dashboard user clicks a filter burns database CPU. Pre-computing features once during ETL moves computation to ingest time, speeding up dashboard queries by **10x**.

### 5. Dual-Layer Caching (Redis + Memory Fallback)
* **Reason**: Executive dashboards often re-query identical date ranges. Caching query results in Redis cuts response time from 150ms to < 1ms. If Redis disconnects or restarts, the application catches the error silently and falls back to a local in-memory Python dictionary cache, ensuring **zero application downtime**.

---

## 5. Hardest Problems I Solved and How

### 1. Pandas 3.0+ `LossySetitemError` during Imputation
* **The Problem**: In Pandas 3.0+, assigning a string like `"GUEST"` to a column inferred as float (due to nulls in raw CSVs) raises `TypeError: Invalid value 'GUEST' for dtype 'float64'`.
* **How I Solved It**: Added defensive type inspection in `DataCleaner`. Before imputing strings, the cleaner checks if the column is numeric; if so, it casts the series to `object` dtype first, guaranteeing seamless compatibility across Pandas 2.x and 3.x.

### 2. Database Insertion Bottleneck (50x Throughput Gain)
* **The Problem**: Inserting records row-by-row via standard ORM loops generated 500,000 individual TCP roundtrips, taking over 15 minutes and timing out database connections.
* **How I Solved It**: Replaced row-by-row loops with SQLAlchemy multi-row chunked inserts (`chunksize=1000, method="multi"`) wrapped inside atomic `with engine.begin():` transaction blocks. Combined with connection pooling (`pool_size=10`), write throughput jumped by **50x** with automatic rollback on failure.

### 3. Silent Encoding Crashes from POS Terminal Exports
* **The Problem**: Real-world retail exports generated by legacy European POS machines contained non-UTF-8 symbols (like `£` British pound signs and accented names), crashing `pd.read_csv()` with `UnicodeDecodeError`.
* **How I Solved It**: Built an automated fallback loop in `DataFileReader` (`utf-8` $\rightarrow$ `latin1` $\rightarrow$ `iso-8859-1` $\rightarrow$ `cp1252`). If a file fails UTF-8, it automatically recovers with `latin1` without human intervention.

### 4. Duplicate Record Ingestion on File Re-runs
* **The Problem**: Re-uploading an updated daily sales export duplicated hundreds of thousands of transactions in the fact table.
* **How I Solved It**: Implemented an automated idempotency firewall: (1) tracked file SHA-256 hashes in `etl_watermarks` to skip unmodified files, and (2) executed left-anti join deduplication against existing database keys (`InvoiceNo + StockCode`) before inserting.

---

## 6. Top 15 Interview Questions & Short Answers

#### Q1: What is RetailLens in one sentence?
> **Answer**: It is an automated retail analytics platform and ETL pipeline that validates messy sales exports, scales compute using hybrid Pandas/PySpark, loads clean records into PostgreSQL 50x faster, and renders real-time Streamlit BI dashboards.

#### Q2: How does your Data Quality Firewall work?
> **Answer**: It acts as an entry gate that evaluates incoming DataFrames against structural rules (mandatory headers) and business rules (non-negative prices, valid dates). Structural failures stop the pipeline immediately, while soft row errors are recorded in a `ValidationReport` audit object.

#### Q3: Why use both Pandas and PySpark?
> **Answer**: They complement each other. Pandas has zero cluster startup latency and is ultra-fast for files under 100MB, but crashes on large files. PySpark scales across clusters for files $\ge$ 100MB, but has JVM startup overhead. My `ComputeRouter` selects the optimal engine dynamically based on file size.

#### Q4: Why did you impute CustomerID as 'GUEST' instead of dropping nulls?
> **Answer**: Missing customer IDs represent guest checkouts. Deleting those rows would permanently remove 25% of total company revenue from the database. Imputing `'GUEST'` keeps revenue totals 100% accurate while allowing customer analytics to filter guest vs. registered buyers.

#### Q5: How did you optimize database write performance by 50x?
> **Answer**: Instead of inserting rows one-by-one, I used SQLAlchemy batch loading with `chunksize=1000` and `method="multi"`, executed inside an atomic transaction context (`with engine.begin():`). This combines 1,000 rows into a single SQL statement, eliminating network roundtrips.

#### Q6: How do you guarantee pipeline idempotency?
> **Answer**: Re-running the pipeline on the same file produces the exact same database state. I enforce this by checking SHA-256 file hashes in `etl_watermarks` and filtering out existing natural business keys (`InvoiceNo`, `StockCode`) before bulk inserting.

#### Q7: What are the benefits of storing data in a Parquet Data Lake?
> **Answer**: Parquet is a Snappy-compressed columnar format. It reduces our raw storage footprint by 68% and allows analytics queries to scan only the necessary columns rather than the whole table, cutting read scan times by 74%.

#### Q8: How does your caching layer handle Redis outages?
> **Answer**: `RedisCache` wraps all Redis operations in try-except blocks. If Redis goes down or experiences a network partition, the client catches the error, logs a warning, and seamlessly falls back to an internal thread-safe in-memory Python dictionary cache with zero downtime.

#### Q9: How do you calculate Month-over-Month (MoM) revenue growth in SQL?
> **Answer**: I use a Common Table Expression (CTE) to aggregate monthly revenue, then apply the `LAG()` window function:
> `((current_revenue - LAG(current_revenue) OVER (ORDER BY month)) / NULLIF(LAG(current_revenue) OVER (ORDER BY month), 0)) * 100`.

#### Q10: What is the difference between Liveness and Readiness probes in your deployment?
> **Answer**: A **Liveness Probe** (`/_stcore/health`) checks if the web process is alive; if it fails, Kubernetes restarts the container. A **Readiness Probe** (`/ready`) verifies database pool health and storage availability; if it fails, traffic is temporarily diverted from that pod without restarting it.

#### Q11: Why did you use a Multi-Stage Docker build?
> **Answer**: A multi-stage build compiles dependencies in a temporary `builder` image and copies only pre-compiled packages into a lightweight `python:3.10-slim` runtime image. This cuts image size by 70% and removes build compilers (`gcc`, `libpq-dev`) from production, hardening security.

#### Q12: How do you prevent SQL injection in your analytical queries?
> **Answer**: All analytical queries in `AnalyticsRepository` strictly use SQLAlchemy parameterized statements (`text("... WHERE country = :country")`). User filter inputs are passed as parameter dictionaries, ensuring the SQL engine treats them as literal values rather than executable code.

#### Q13: What is the difference between `DENSE_RANK()` and `RANK()` in your top products query?
> **Answer**: `RANK()` leaves gaps in rank numbers if there is a tie (e.g., 1, 1, 3), whereas `DENSE_RANK()` does not leave gaps (e.g., 1, 1, 2). I use `DENSE_RANK()` so our top product leaderboards always display contiguous ranking.

#### Q14: How does your pipeline handle cancelled or returned retail orders?
> **Answer**: In retail, cancellations start with a 'C' in `InvoiceNo` and have negative `Quantity`. The pipeline flags these as `IsCancellation = TRUE` during feature engineering and computes separate cancellation KPIs, preventing returns from polluting positive sales metrics.

#### Q15: How does CI/CD enforce production quality before deployment?
> **Answer**: Our GitHub Actions pipeline automatically triggers on every pull request to `main`. It runs the entire 83-test unit and integration suite, verifies environment configuration, and tests Docker container builds. If any test fails, deployment is automatically blocked.

---

## 7. 3 Weak Spots an Interviewer Could Challenge & How to Answer Honestly

### Challenge 1: *"Routing by file size (100MB) is naive. What if a 50MB file has 50 columns with huge text?"*
* **Honest Answer**:  
  > *"That is a completely fair point. File size on disk is an approximation for memory footprint, but uncompressed in-memory expansion depends on column count and data types. In a future iteration, I would inspect dataset shape (`rows * columns`) and estimated DataFrame in-memory byte size via `sys.getsizeof` or sample partition profiling rather than relying solely on raw file size."*

### Challenge 2: *"Checking for duplicates against the database in Python scales poorly for 50 million rows."*
* **Honest Answer**:  
  > *"You're right. Querying existing natural keys via left-anti joins works smoothly for hundreds of thousands of rows, but at 50 million rows, in-memory sets and index queries create high database load. For true big-data scale, I would load incoming batches directly into an un-indexed staging table in PostgreSQL and perform an idempotent `INSERT INTO fact_sales ... ON CONFLICT DO NOTHING` inside the database engine, or use a Bloom filter."*

### Challenge 3: *"Streamlit is great for prototypes, but it cannot handle thousands of concurrent enterprise users."*
* **Honest Answer**:  
  > *"I agree. Streamlit was chosen because it allowed me to build an interactive BI dashboard and pipeline monitor rapidly in pure Python. However, because RetailLens was designed with strict modularity, the UI is decoupled from the business logic. We already have a REST API dispatcher in `api/app.py`, so we could easily replace Streamlit with a Next.js/React frontend backed by FastAPI without rewriting any data pipeline or database code."*

---

## 8. Numbers to Remember (Quick Cheat Sheet)

* **Dataset Size**: **541,909** raw transactions (UCI Online Retail dataset), ~**45MB** uncompressed CSV.
* **Guest Imputation**: **135,080** rows (**~25%**) lacked `CustomerID`, safely imputed as `'GUEST'`, preserving **£1.7M+** in revenue.
* **Cancellations**: **8,905** orders (**~1.8%**) flagged with `IsCancellation = TRUE`.
* **Feature Count**: **17** total columns (**8** raw ingested + **9** engineered features).
* **Test Suite**: **83 automated unit/integration tests** across **31** test modules with **100% pass rate**.
* **Storage Reduction**: **68.4%** file compression using Snappy Parquet (from ~45MB to ~14MB); **74.2%** faster query scan speed.
* **Database Write Speed**: **50x faster** write throughput using `chunksize=1000` multi-row batch inserts vs single-row inserts.
* **Cache Latency**: **< 1ms** response time on Redis cache hit vs **80–250ms** direct PostgreSQL query (5-minute TTL).
* **Docker Image**: **70%** reduction in image size via multi-stage build on `python:3.10-slim`.
* **Autoscaling Target**: **2 to 10** container pod replicas triggered when CPU exceeds **75%** or memory exceeds **80%** via Kubernetes HPA.
