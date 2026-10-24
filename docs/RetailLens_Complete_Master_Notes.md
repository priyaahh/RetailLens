# RETAILLENS — COMPLETE MASTER NOTES

---

## 1. Project Overview

### What RetailLens Is
**RetailLens** is an enterprise-grade, end-to-end retail analytics platform and distributed data engineering infrastructure built using **Python, PySpark, PostgreSQL, Streamlit, Docker, Kubernetes, Prometheus, Redis, and GitHub Actions**. It automates the ingestion, validation, cleaning, transformation, feature engineering, data lake storage, relational persistence, and interactive visualization of raw e-commerce sales transactions.

### Problem Statement
Modern retail and e-commerce organizations process millions of transactional line items daily, exported from heterogeneous point-of-sale (POS) systems and web platforms. These datasets routinely suffer from:
* **Data Quality Anomalies**: Non-UTF-8 character encodings (e.g. `latin1`, `cp1252` currency symbols like `£`), missing values, corrupted headers, duplicate line items, negative unit prices, and invalid timestamps.
* **Scalability Bottlenecks**: Single-node memory limits (OOM crashes on files $>2$GB) and unoptimized, single-threaded parsing.
* **Lack of Data Governance & Observability**: Silent data corruption, missing audit logs, lack of data lineage, and poor pipeline failure visibility.
* **Slow Analytical Queries**: Computing complex aggregates (e.g., Month-over-Month growth, customer lifetime value, cancellation rates) on-the-fly in web applications or un-indexed databases creates extreme CPU bottlenecks.

### Objective
RetailLens bridges the gap between raw, messy transactional files and enterprise executive decision-making by delivering:
1. A **defensive Data Quality Firewall** that validates structural schemas and semantic business rules before data reaches persistence.
2. A **Hybrid Compute Routing Engine** that dynamically routes datasets between Pandas (for small files $<100$MB) and Apache Spark / PySpark (for distributed big data scale $\ge 100$MB).
3. A **Temporal Parquet Data Lake** and a **Cloud PostgreSQL Relational Data Warehouse** with connection pooling and chunked batch loading.
4. An **Idempotent, Watermarked Incremental ETL Pipeline** with audit run tracking, data lineage provenance, and Dead Letter Queue isolation.
5. An **Analytics & KPI Engine** powering a responsive **Streamlit Business Intelligence Dashboard**, production REST API boundary, Prometheus metrics exporter, and Redis zero-downtime cache.
6. A **Containerized, Kubernetes-ready Cloud Deployment** hardened with non-root security contexts, CI/CD automation, and zero-downtime rolling updates.

### What the System Does
* **Ingests**: Accepts raw tabular transaction datasets (`.csv`, `.xlsx`, `.xls`) with automated multi-encoding fallback (`utf-8` $\rightarrow$ `latin1` $\rightarrow$ `iso-8859-1` $\rightarrow$ `cp1252`) and pre-read file size guardrails ($100$MB limit).
* **Validates**: Executes structural schema assertions (fail-fast `SchemaValidationError`) and soft row-level business rule checks, generating a `ValidationReport` audit dataclass.
* **Cleans**: Strips whitespace, normalizes string casing, imputes missing `CustomerID` to `'GUEST'` (preserving $25\%$ of total sales revenue), filters invalid negative prices, and drops duplicate composite records.
* **Transforms**: Pre-computes line-item total prices (`Quantity * UnitPrice`), temporal date attributes (`InvoiceYear`, `InvoiceMonth`, `InvoiceQuarter`, `InvoiceWeekday`, `InvoiceHour`), cancellation flags (`IsCancellation`), customer segment classifications (`CustomerType`), and binned spend buckets (`RevenueBucket`).
* **Stores**: Manages raw, staged, and processed zones in a Snappy-compressed Parquet Data Lake (`year=YYYY/month=MM`) and persists fact tables into Neon Cloud PostgreSQL with B-Tree indexes.
* **Analyzes & Visualizes**: Calculates 25+ business KPIs (Total Revenue, AOV, Cancellation Rate %, Top Products, MoM Growth) via parameterized SQL queries and exposes them through Streamlit charts, REST endpoints, and Prometheus metrics.

### Key Features
* 🐋 **Multi-Stage Containerization**: 2-stage production `Dockerfile` running as non-root user (`appuser` UID `10001`) with HTTP healthchecks.
* ⚡ **Hybrid Compute Router**: `ComputeRouter` dynamically evaluates file size to select between single-node Pandas and distributed PySpark execution.
* 🌲 **Parquet Data Lake**: Snappy-compressed columnar lake managed by `ParquetDataLake` with temporal partitioning.
* ☁️ **Cloud Storage Abstraction**: `StorageBackend` interface with `CloudStorageBackend` supporting S3-compatible cloud object storage with in-memory mock fallback.
* 🐘 **Database Connection Pooling**: `create_pooled_engine()` and `check_db_health()` with pre-ping validation (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`).
* ⚡ **Redis & Memory Fallback Cache**: `RedisCache` with key TTL expiration, hit/miss tracking, and zero-downtime memory fallback.
* 🔌 **REST API Boundary**: `RetailLensAPI` (`api/app.py`) providing `/health`, `/ready`, `/metrics`, `/pipeline/runs`, `/pipeline/quality`, and `/analytics/kpis`.
* 📊 **Prometheus Operational Metrics**: `PrometheusMetricsExporter` exporting standard exposition text metrics.
* ☸️ **Kubernetes Manifests**: Complete K8s architecture containing Namespace, ConfigMap, Secret, Deployment, Service, Ingress TLS, and HPA autoscaling.
* 🤖 **Multi-Stage CI/CD**: GitHub Actions CI workflow (`ci.yml`) automating linting, full test suite execution (31 test modules), and Docker build validation.

---

## 2. Complete Tech Stack

| Technology | Where Used in RetailLens | Why Used | How It Fits Into RetailLens Architecture |
| :--- | :--- | :--- | :--- |
| **Python (3.10)** | Entire backend, ETL, API, and UI | Unified ecosystem for Data Engineering, Pandas, PySpark, SQLAlchemy, and Streamlit. | Primary programming language across all application modules. |
| **Pandas (2.0+)** | `ingestion/reader.py`, `cleaner.py`, `transformer.py`, `validator.py` | Vectorized in-memory tabular manipulation for datasets under 100MB. | Core compute engine for single-node ETL processing. |
| **PySpark (3.5+)** | `ingestion/spark_transformer.py` | Distributed Catalyst-optimized cluster execution for big data scale ($\ge 100$MB). | Big data scale-out processing module in hybrid compute architecture. |
| **PostgreSQL (15+)** | `database/`, Neon Cloud PostgreSQL | Production ACID-compliant relational data warehouse with B-Tree indexing, CTEs, and window functions. | Persistence layer storing `fact_sales`, audit tables, and views. |
| **SQLAlchemy (2.0+)** | `database/connection.py`, `database/pool.py`, `ingestion/loader.py` | ORM & DB engine providing connection pooling, dialect abstraction, SQL injection prevention, and `to_sql()` batch loading. | Bridge between Python Pandas DataFrames and PostgreSQL database. |
| **Streamlit (1.30+)** | `app/main.py`, `app/pages/` | Pure-Python interactive web application framework for rapid BI UI development. | Application frontend rendering executive dashboards and operational monitors. |
| **Plotly (5.18+)** | `dashboard/charts.py` | Interactive JavaScript chart rendering with tooltips, panning, and zooming inside browser. | Charting engine embedded inside Streamlit dashboard views. |
| **FastAPI / REST API** | `api/app.py` | Production HTTP REST API interface for external service integration and container probes. | REST API boundary exposing system readiness, health, and analytical endpoints. |
| **Redis (7.0+)** | `analytics/cache.py` | High-speed, in-memory key-value cache with TTL expiration for analytical queries. | Caching layer reducing database load with automatic in-memory fallback. |
| **Prometheus Exporter** | `analytics/metrics.py` | Standardized operational metrics exporter in Prometheus exposition text format. | Observability module reporting pipeline throughput, error rates, and cache hits. |
| **Docker & Docker Compose** | `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Multi-stage containerization isolating runtime environment and dependencies. | Container packaging for local execution and Kubernetes deployment. |
| **Kubernetes (k8s)** | `deploy/kubernetes/` | Production container orchestration, service discovery, ingress TLS, and horizontal autoscaling. | Deployment target running container pods with HPA and rolling updates. |
| **GitHub Actions** | `.github/workflows/ci.yml` | Continuous Integration automating linting, 31 test modules, and Docker build checks. | CI/CD gate blocking broken code from merging to `main` or deploying. |
| **Apache Parquet & PyArrow** | `storage/parquet_lake.py` | Snappy-compressed columnar file format partitioned by `year=YYYY/month=MM`. | Storage format for raw, staged, and processed Data Lake zones. |
| **Boto3 / Cloud Storage** | `storage/cloud.py` | Abstract cloud object storage backend interface for S3/GCS compatibility. | Persistence layer for Data Lake files in cloud environments. |

---

## 3. Complete Architecture

### System Architecture Flow

```text
                                raw_dataset.csv / .xlsx
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │    Ingestion & Data Quality Boundary │
                      │  - DataFileReader (File Guardrails)  │
                      │  - Multi-Encoding Fallback Loop      │
                      │  - DataValidator (Quality Firewall)  │
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │    Hybrid Compute Routing Engine     │
                      │  - ComputeRouter (File Size Check)   │
                      │   ├─ < 100MB  ──► Pandas Engine      │
                      │   └─ >= 100MB ──► PySpark Engine     │
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │     Cleaning & Transformation        │
                      │  - DataCleaner (Sanitize & Impute)   │
                      │  - DataTransformer (Features & Dates)│
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │    Parquet Data Lake Storage Zone    │
                      │  - ParquetDataLake (Snappy / Partition)│
                      │  - CloudStorageBackend (S3/GCS)      │
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │   Idempotent Database Loading Layer  │
                      │  - DatabaseLoader (Anti-Join Filter) │
                      │  - SQLAlchemy Pool (1000 Multi-Batch)│
                      │  - Atomic Transaction (Auto-Rollback)│
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │   Neon Cloud PostgreSQL Data Warehouse│
                      │  - fact_sales Table & B-Tree Indexes │
                      │  - pipeline_runs & data_lineage      │
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │     Analytics & Service API Layer    │
                      │  - SQLAnalyticsService (queries.sql) │
                      │  - KPICalculator & KPIEngine         │
                      │  - InsightEngine (Alert Thresholds)  │
                      │  - RedisCache & PrometheusMetrics    │
                      └───────────────────┬──────────────────┘
                                          │
                                          ▼
                      ┌──────────────────────────────────────┐
                      │    Streamlit BI Web Application      │
                      │  - Executive Dashboard Views         │
                      │  - Plotly Interactive Visualizations │
                      │  - Pipeline Operational Monitor      │
                      └──────────────────────────────────────┘
```

### Complete End-to-End Data Pipeline Flow
```text
Raw Data ──► Ingestion ──► Validation ──► Cleaning ──► Transformation ──► Database ──► Analytics ──► KPIs ──► Insights ──► Dashboard
```

---

## 4. Complete Folder Structure

```text
RetailLens/
├── .github/
│   └── workflows/
│       └── ci.yml                      # GitHub Actions multi-stage CI/CD pipeline
├── analytics/
│   ├── __init__.py
│   ├── cache.py                        # RedisCache with zero-downtime memory fallback
│   ├── insights.py                     # InsightEngine evaluating business alert rules
│   ├── kpi_engine.py                   # KPIEngine calculating formatted metric cards
│   ├── kpis.py                         # KPICalculator running scalar DB aggregations
│   ├── metrics.py                      # PrometheusMetricsExporter operational metrics
│   ├── pipeline_service.py             # Operational monitoring pipeline service
│   ├── repository.py                   # AnalyticsRepository executing parameterized SQL
│   ├── service.py                      # AnalyticsService composed application layer
│   └── sql_analytics.py                # SQLAnalyticsService executing queries.sql
├── api/
│   ├── __init__.py
│   └── app.py                          # RetailLensAPI production REST API boundary
├── app/
│   ├── __init__.py
│   ├── main.py                         # Streamlit multi-page router & layout entry
│   ├── components/                     # Reusable UI component modules
│   └── pages/                          # Specialized UI view pages (Pipeline Monitor, etc.)
├── assets/                             # Static visual branding assets and logos
├── config/
│   ├── __init__.py
│   ├── app_config.py                   # AppConfig typed environment profiles & security
│   ├── logging_config.py               # Rotating log setup with SensitiveDataFilter
│   └── schema_config.py                # IngestionConfig schema contracts & limits
├── data/                               # Staging data lake storage (gitignored)
│   ├── archive/                        # Historical raw dataset backups
│   ├── invalid/                        # Quarantine directory for bad input files
│   ├── processed/                      # Staged clean CSV/Parquet outputs
│   └── raw/                            # Ingestion drop zone for raw incoming files
├── database/
│   ├── __init__.py
│   ├── connection.py                   # Legacy SQLAlchemy engine builder
│   ├── pool.py                         # Production create_pooled_engine() & pre-ping
│   ├── queries.sql                     # Master SQL catalog of 25 analytical queries
│   ├── retry.py                        # Exponential backoff retry handler
│   └── schema.sql                      # DDL schema definitions, indexes, and views
├── deploy/
│   └── kubernetes/                     # Kubernetes manifest production configurations
│       ├── configmap.yaml
│       ├── deployment.yaml
│       ├── hpa.yaml
│       ├── ingress.yaml
│       ├── namespace.yaml
│       ├── secret.example.yaml
│       └── service.yaml
├── docs/                               # 36 comprehensive markdown documentation files
├── etl/                                # Submodule aliases and legacy pipeline scripts
├── ingestion/
│   ├── __init__.py
│   ├── benchmark.py                    # Performance benchmarking engine (Pandas vs Spark)
│   ├── cleaner.py                      # DataCleaner vectorized string sanitization
│   ├── compute_router.py              # Hybrid ComputeRouter selecting execution engine
│   ├── lineage.py                      # DataLineageTracker tracking source-to-target provenance
│   ├── loader.py                       # DatabaseLoader anti-join batch loading
│   ├── pipeline.py                     # ETLPipeline stage orchestrator
│   ├── quality_monitor.py             # DataQualityMonitor calculating quality scores
│   ├── reader.py                       # DataFileReader multi-encoding defensive reader
│   ├── spark_transformer.py            # SparkDataTransformer distributed PySpark engine
│   ├── tracker.py                      # PipelineRunTracker audit execution database logger
│   ├── transformer.py                  # DataTransformer Pandas feature engineering
│   ├── validator.py                    # DataValidator schema & business rule firewall
│   └── watermark.py                    # WatermarkManager SHA-256 hash & high-watermark bounds
├── logs/                               # Application runtime log outputs
├── orchestration/
│   ├── __init__.py
│   ├── dag.py                          # PipelineDAG workflow dependency DAG
│   ├── scheduler.py                    # PipelineScheduler cron & event trigger engine
│   ├── tasks.py                        # Task operator definitions for Airflow/Prefect
│   └── workflow.py                     # OrchestratedPipelineWorkflow execution context
├── reports/                            # Power BI (.pbix) reports and executive export artifacts
├── storage/
│   ├── __init__.py
│   ├── base.py                         # StorageBackend abstract interface contract
│   ├── cloud.py                        # CloudStorageBackend S3/GCS cloud object storage
│   ├── local.py                        # LocalStorageBackend local filesystem storage
│   └── parquet_lake.py                 # ParquetDataLake raw/staged/processed lake zones
├── tests/                              # 31 unit & integration test modules (77 tests)
├── .dockerignore                       # Excludes local files from Docker build context
├── .env.example                        # Template environment configuration secrets
├── Dockerfile                          # 2-stage multi-stage production Docker image
├── docker-compose.yml                  # Local multi-container Docker deployment config
├── README.md                           # Master project README file
└── requirements.txt                    # Pinned Python package dependencies
```

---

## 5. Data Ingestion

### DataFileReader Boundary
Primary Module: [`ingestion/reader.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/reader.py)  
Core Class: `DataFileReader`

The ingestion layer acts as a defensive entry boundary designed to reject invalid files before system resources are consumed.

### Pre-Read Metadata Guardrails
To protect application memory against Out-of-Memory (OOM) attacks or server crashes, `DataFileReader.validate_file_metadata()` asserts:
1. **File Existence**: Verifies that the path exists on disk (`path.exists()`).
2. **Supported Extension Check**: Restricts input extensions to `SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}`.
3. **File Size Limit Guardrail**: Enforces `MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024` ($100$MB). Files exceeding $100$MB are rejected before attempting parsing into RAM.

### Multi-Encoding Fallback Loop
Raw CSV exports from legacy point-of-sale (POS) systems frequently contain non-ASCII characters (e.g., `£` currency symbols or accented customer names) encoded in non-UTF-8 character sets. A naive `pd.read_csv()` using default UTF-8 raises a `UnicodeDecodeError` and crashes the application.

RetailLens solves this with an automated multi-encoding fallback loop inside `_read_csv_with_fallback()`:
```python
ENCODING_FALLBACKS = ["utf-8", "latin1", "iso-8859-1", "cp1252"]

for encoding in ENCODING_FALLBACKS:
    try:
        df = pd.read_csv(file_path, encoding=encoding, **kwargs)
        logger.info("Successfully parsed CSV using encoding: %s", encoding)
        return df
    except (UnicodeDecodeError, Exception) as e:
        logger.warning("Encoding %s failed: %s. Retrying next encoding...", encoding, str(e))
raise ValueError(f"Failed to decode file '{file_path}' using supported encodings.")
```

### Header & Schema Enforcement
`DataFileReader.validate_header()` inspects the raw column headers against `IngestionConfig.REQUIRED_COLUMNS`:
* Mandatory headers required: `["InvoiceNo", "StockCode", "Quantity", "InvoiceDate", "UnitPrice"]`.
* Rejects empty DataFrames, duplicate column headers, and files missing required columns.

### Quarantine Management
Corrupt or unparseable files are logged and automatically isolated in `data/invalid/` for developer investigation while preventing pipeline breakage.

---

## 6. Data Validation & Data Quality

Primary Module: [`ingestion/validator.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/validator.py)  
Core Classes: `DataValidator`, `ValidationReport`, `SchemaValidationError`, `BusinessRuleValidationError`

### Data Quality Firewall Concept
A Data Quality Firewall is an automated inspection gate that evaluates raw tabular data immediately after reading. It enforces strict data contracts before records enter the transformation pipeline or persistence store.

### Hard vs. Soft Validation Strategy
* **Hard Structural Schema Errors**: Severe structural defects (empty DataFrame, duplicate headers, missing mandatory columns) render data unparseable. These throw a `SchemaValidationError` immediately (**fail-fast strategy**) to halt execution before wasting CPU.
* **Soft Business Rule Anomalies**: Row-level anomalies (e.g. negative unit price, unparseable date format, missing customer ID) represent invalid data rows. Instead of crashing the entire pipeline on a single bad row, these anomalies are accumulated inside a `ValidationReport` dataclass while valid rows proceed.

### ValidationReport Dataclass
```python
@dataclass
class ValidationReport:
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    is_valid: bool = True
    error_counts: Dict[str, int] = field(default_factory=dict)
    error_summary: List[str] = field(default_factory=list)

    def add_error(self, category: str, count: int, message: str) -> None:
        self.error_counts[category] = self.error_counts.get(category, 0) + count
        self.error_summary.append(f"[{category}] {message} (Affected Rows: {count})")
        if count > 0:
            self.invalid_rows = min(self.total_rows, self.invalid_rows + count)

    def finalize(self) -> None:
        self.valid_rows = max(0, self.total_rows - self.invalid_rows)
        self.is_valid = len(self.error_counts) == 0 or self.invalid_rows == 0

    @property
    def passed_rows(self) -> int:
        return self.valid_rows

    @property
    def failed_rows(self) -> int:
        return self.invalid_rows
```

### Vectorized Validation Logic
Validation checks run using Pandas vectorized Series operations (`isna()`, `to_numeric()`, boolean masks), executing over 100x faster than row-by-row Python loops:
1. `_validate_schema_structure()`: Asserts non-empty, checks header uniqueness, and validates mandatory column presence.
2. `_validate_types_and_formats()`: Evaluates datetime string parseability (`pd.to_datetime(..., errors="coerce")`) and flags non-numeric values in numeric columns (`Quantity`, `UnitPrice`).
3. `_validate_business_rules()`: Flags missing invoice identifiers (`MISSING_INVOICE_NO`), negative prices (`NEGATIVE_UNIT_PRICE`), future timestamps (`FUTURE_INVOICE_DATE`), and logs returns (`Quantity < 0`).

---

## 7. Cleaning & Transformation

Primary Modules: [`ingestion/cleaner.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/cleaner.py), [`ingestion/transformer.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/transformer.py)  
Core Classes: `DataCleaner`, `DataTransformer`

### Validation vs. Cleaning vs. Transformation Explained
* **Validation**: Inspecting and auditing data against contracts without modifying values. Outputs a pass/fail report and quality metrics.
* **Cleaning (Sanitization)**: Standardizing text formatting, stripping whitespace, imputing missing values, removing corrupt records, and deduplicating rows.
* **Transformation (Enrichment)**: Pre-computing derived analytical features, temporal date parts, business flags, and spend categorizations.

### DataCleaner Implementation
1. **String Whitespace & Case Normalization**:
   * Trims whitespace: `df[col] = df[col].astype(str).str.strip()`
   * Uppercase formatting: `StockCode` and `InvoiceNo` converted to uppercase.
   * Title case formatting: `Country` converted to title case.
2. **Domain-Specific Null Imputation**:
   * Missing `CustomerID` imputed to `'GUEST'`.
   * Missing `Description` imputed to `'UNKNOWN DESCRIPTION'`.
   * *Why Impute `CustomerID = 'GUEST'` instead of dropping?* In retail datasets, missing customer IDs represent guest checkouts. Indiscriminately running `dropna(subset=['CustomerID'])` would delete $25\%$ of total sales revenue data, completely warping total sales metrics!
3. **Record Deduplication & Filtering**:
   * Filters out invalid negative prices (`UnitPrice < 0`).
   * Drops exact duplicate records across composite keys `["InvoiceNo", "StockCode", "Quantity", "InvoiceDate", "CustomerID"]`.

### DataTransformer Implementation & Feature Pre-computation
Pre-computing analytical attributes during ETL shifts expensive CPU calculations from read-time (SQL/Dashboard) to ingest-time, accelerating downstream dashboard rendering by 10x:
* `TotalPrice`: `round(Quantity * UnitPrice, 2)`
* Temporal Date Parts: `InvoiceYear`, `InvoiceMonth`, `InvoiceQuarter`, `InvoiceWeekday`, `InvoiceHour`.
* `IsCancellation`: Boolean flag (`True` if `Quantity < 0` or `InvoiceNo` starts with `'C'`).
* `CustomerType`: Categorical classification (`'Registered'` if `CustomerID != 'GUEST'` else `'Guest'`).
* `RevenueBucket`: Binned spend categories created via `np.select()`:
  * `Quantity < 0` $\rightarrow$ `'Cancellation'`
  * `TotalPrice < 10` $\rightarrow$ `'Low (< £10)'`
  * `10 <= TotalPrice <= 50` $\rightarrow$ `'Medium (£10-£50)'`
  * `TotalPrice > 50` $\rightarrow$ `'High (> £50)'`

---

## 8. Complete ETL Pipeline

Primary Module: [`ingestion/pipeline.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/pipeline.py)  
Core Classes: `ETLPipeline`, `PipelineConfig`, `PipelineResult`

```text
Extract (DataFileReader)
   │
   ▼
Validate (DataValidator)
   │
   ▼
Clean (DataCleaner)
   │
   ▼
Transform (DataTransformer)
   │
   ▼
Load (DatabaseLoader -> PostgreSQL)
```

### Decoupled Orchestration Architecture
`ETLPipeline` operates strictly as a stage orchestrator. Adhering to the **Single Responsibility Principle (SRP)**, it contains zero string manipulation or validation logic. Adhering to **Dependency Injection (DI)**, all stage handlers are injected via `__init__()`:

```python
class ETLPipeline:
    def __init__(
        self,
        reader: Optional[DataFileReader] = None,
        validator: Optional[DataValidator] = None,
        cleaner: Optional[DataCleaner] = None,
        transformer: Optional[DataTransformer] = None,
        loader: Optional[DatabaseLoader] = None,
        watermark_mgr: Optional[WatermarkManager] = None,
        tracker: Optional[PipelineRunTracker] = None,
        lineage_tracker: Optional[DataLineageTracker] = None,
        quality_monitor: Optional[DataQualityMonitor] = None,
        config: Optional[PipelineConfig] = None,
    ):
        self.reader = reader or DataFileReader()
        self.validator = validator or DataValidator()
        self.cleaner = cleaner or DataCleaner()
        self.transformer = transformer or DataTransformer()
        self.loader = loader or DatabaseLoader()
        self.watermark_mgr = watermark_mgr or WatermarkManager()
        self.tracker = tracker or PipelineRunTracker()
        self.lineage_tracker = lineage_tracker or DataLineageTracker()
        self.quality_monitor = quality_monitor or DataQualityMonitor()
        self.config = config or PipelineConfig()
```

### Complete Stage Execution Walkthrough
1. **Stage 0 (Watermark & Hash Check)**: Computes SHA-256 file hash and checks `et_watermarks` for duplicate execution.
2. **Stage 1 (Extract & Filter)**: `DataFileReader.read_file()` parses raw tabular data. `WatermarkManager.filter_incremental_dataframe()` filters out historical records already loaded.
3. **Stage 2 (Validate)**: `DataValidator.validate()` executes schema and business rule assertions, returning a `ValidationReport`.
4. **Stage 3 (Clean)**: `DataCleaner.clean()` sanitizes text, imputes guest IDs, and deduplicates records.
5. **Stage 4 (Transform)**: `DataTransformer.transform()` pre-computes derived features and date attributes.
6. **Stage 5 (Load & Audit)**: `DatabaseLoader.load()` performs left anti-joins against PostgreSQL natural keys to prevent duplicates, inserting batch rows (`chunksize=1000`) inside an atomic transaction block. Records audit runs in `pipeline_runs` and data lineage in `data_lineage`.

---

## 9. Database & SQL

Primary Modules: [`database/schema.sql`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/database/schema.sql), [`database/queries.sql`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/database/queries.sql), [`database/pool.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/database/pool.py), [`ingestion/loader.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/ingestion/loader.py)

### Database Choice: Managed Cloud PostgreSQL (Neon DB)
RetailLens utilizes **Neon Cloud PostgreSQL** as its production relational warehouse. PostgreSQL provides ACID-compliant transactions, robust ANSI SQL CTE/window function support, native B-Tree indexing, and multi-version concurrency control (MVCC).

### Target DDL Schema (`fact_sales`)
```sql
CREATE TABLE fact_sales (
    transaction_id BIGSERIAL PRIMARY KEY,
    invoice_no VARCHAR(20) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity != 0),
    unit_price NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0.00),
    total_amount NUMERIC(12,2) NOT NULL,
    invoice_timestamp TIMESTAMP NOT NULL,
    invoice_year SMALLINT NOT NULL,
    invoice_month SMALLINT NOT NULL CHECK (invoice_month BETWEEN 1 AND 12),
    invoice_quarter SMALLINT NOT NULL CHECK (invoice_quarter BETWEEN 1 AND 4),
    day_of_week VARCHAR(10) NOT NULL,
    invoice_hour SMALLINT NOT NULL CHECK (invoice_hour BETWEEN 0 AND 23),
    customer_id VARCHAR(20) NOT NULL DEFAULT 'GUEST',
    customer_type VARCHAR(20) NOT NULL DEFAULT 'Guest',
    country VARCHAR(50) NOT NULL,
    is_cancellation BOOLEAN NOT NULL DEFAULT FALSE,
    revenue_bucket VARCHAR(30) NOT NULL,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analytical B-Tree Index Catalog
CREATE INDEX idx_fact_sales_invoice_no ON fact_sales(invoice_no);
CREATE INDEX idx_fact_sales_customer_id ON fact_sales(customer_id);
CREATE INDEX idx_fact_sales_stock_code ON fact_sales(stock_code);
CREATE INDEX idx_fact_sales_timestamp ON fact_sales(invoice_timestamp);
CREATE INDEX idx_fact_sales_country ON fact_sales(country);
CREATE INDEX idx_fact_sales_year_month ON fact_sales(invoice_year, invoice_month);
```

### Key Analytical SQL Queries (`database/queries.sql`)

#### 1. Average Order Value (AOV) with `NULLIF` Protection
```sql
SELECT 
    ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2) AS average_order_value
FROM fact_sales
WHERE is_cancellation = FALSE;
```

#### 2. Cancellation Rate %
```sql
SELECT 
    ROUND((COUNT(DISTINCT CASE WHEN is_cancellation = TRUE THEN invoice_no END)::NUMERIC / 
           NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2) AS cancellation_rate_pct
FROM fact_sales;
```

#### 3. Month-over-Month (MoM) Growth Rate (CTE + `LAG()` Window Function)
```sql
WITH monthly_revenue AS (
    SELECT 
        invoice_year, 
        invoice_month, 
        SUM(total_amount) AS current_revenue
    FROM fact_sales 
    WHERE is_cancellation = FALSE
    GROUP BY invoice_year, invoice_month
)
SELECT 
    invoice_year, 
    invoice_month, 
    current_revenue,
    LAG(current_revenue, 1) OVER (ORDER BY invoice_year, invoice_month) AS previous_month_revenue,
    ROUND(((current_revenue - LAG(current_revenue, 1) OVER (ORDER BY invoice_year, invoice_month)) / 
           NULLIF(LAG(current_revenue, 1) OVER (ORDER BY invoice_year, invoice_month), 0)) * 100, 2) AS mom_growth_pct
FROM monthly_revenue;
```

#### 4. Top 3 Products per Country (`DENSE_RANK()` Window Function)
```sql
WITH product_ranks AS (
    SELECT 
        country, 
        stock_code, 
        description, 
        SUM(total_amount) AS total_revenue,
        DENSE_RANK() OVER (PARTITION BY country ORDER BY SUM(total_amount) DESC) AS rank
    FROM fact_sales 
    WHERE is_cancellation = FALSE
    GROUP BY country, stock_code, description
)
SELECT country, rank, stock_code, description, total_revenue
FROM product_ranks 
WHERE rank <= 3;
```

### Database Persistence & Connection Pooling
`DatabaseLoader` maps Pandas feature names to PostgreSQL column names using `COLUMN_MAPPING`. Persistence is managed via `create_pooled_engine()` in `database/pool.py`:
* `pool_size = 10`, `max_overflow = 20`, `pool_timeout = 30`, `pool_recycle = 1800`.
* `pool_pre_ping = True` (issues a test ping before checking out connections to prevent stale socket errors).
* **Chunked Batch Loading**: `df.to_sql(name=table_name, con=conn, if_exists="append", index=False, chunksize=1000, method="multi")`. Grouping 1,000 rows into multi-row SQL payloads increases write throughput by over 50x compared to single-row loops.
* **ACID Transaction Safety**: Executed inside `with self.engine.begin() as conn:`. Automatically commits on success and executes a `ROLLBACK` on error.

---

## 10. Analytics & KPI Engine

Primary Modules: [`analytics/service.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/service.py), [`analytics/repository.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/repository.py), [`analytics/kpi_engine.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/kpi_engine.py), [`analytics/insights.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/insights.py), [`analytics/cache.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/analytics/cache.py)

### Component Architecture

```text
Streamlit UI Page / REST API
           │
           ▼
   AnalyticsService (service.py)
           │
     ┌─────┴────────────────────────────┐
     ▼                                  ▼
KPIEngine (kpi_engine.py)     InsightEngine (insights.py)
     │                                  │
     └─────────────────┬────────────────┘
                       │
                       ▼
         AnalyticsRepository (repository.py)
                       │
                       ▼
       RedisCache (analytics/cache.py) ──► Neon PostgreSQL DB
```

### Component Details
1. **AnalyticsRepository**: Encapsulates SQL query execution using parameterized `text()` SQL bindings and connection pooling. Supports filtering by date range, country, customer type, and cancellation status.
2. **KPICalculator & KPIEngine**: Computes formatted scalar business metrics (Total Revenue, Total Orders, Units Sold, Unique Customers, AOV, Cancellation Rate %) with zero/null safety wrappers.
3. **InsightEngine**: Automated rule engine that evaluates metric DataFrames against threshold parameters (`cancellation_rate_threshold=5.0%`). Generates `Insight` objects classified by severity (`INFO`, `WARNING`, `CRITICAL`) with actionable recommendations.
4. **RedisCache**: High-speed caching layer (`analytics/cache.py`) supporting TTL key expiration and hit/miss tracking. Includes zero-downtime memory fallback when Redis server is unreachable.

---

## 11. Dashboard / Visualization

Primary Modules: [`app/main.py`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/app/main.py), `app/pages/`, `dashboard/charts.py`

### Streamlit Web Application Architecture
RetailLens features a multi-page, pure-Python web dashboard designed for executive stakeholders and data engineers.

### Dashboard Layout & Navigation Router (`app/main.py`)
* Sidebar controls feature dynamic filter selections: Date Range Pickers, Country Dropdowns, Customer Type Selectors, and Cancellation Toggles.
* Navigates across specialized view pages:
  1. `Overview`: High-level executive summary KPI cards, revenue trends, and critical insight alerts.
  2. `Sales Analytics`: Detailed time-series trend lines, day-of-week heatmaps, and hourly breakdown charts.
  3. `Product Performance`: Product revenue leaderboards, sales volume bar charts, and category distribution pie charts.
  4. `Customer Insights`: Registered vs Guest spending breakdown, customer cohort lifetime value, and order frequency distributions.
  5. `Pipeline Monitor`: Operational observability tab displaying system health badges, latest run status, execution duration, quality scores, and data lineage.

### Caching Optimization & Data Flow
To prevent expensive database queries on every user interaction, Streamlit views utilize two-tier caching:
* `@st.cache_resource`: Persists database connection pools and API singletons across user sessions.
* `@st.cache_data(ttl=300)`: Caches query DataFrame results for 5 minutes, eliminating redundant database calls during interactive filter adjustments.

---

## 12. Testing

Primary Directory: [`tests/`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/tests)  
Test Suite: 31 dedicated test modules containing 77 unit and integration tests.

```bash
# Execute entire test suite
python -m unittest discover tests -v
```

### Comprehensive Test Module Inventory

| Test Module | Component Tested | Failure / Edge Case Scenarios Caught |
| :--- | :--- | :--- |
| `test_ingestion.py` | `DataFileReader` | Non-existent paths (`FileNotFoundError`), unsupported `.txt` extensions, missing mandatory headers, and multi-encoding fallback parsing. |
| `test_validator.py` | `DataValidator` | Empty DataFrames, duplicate column headers, missing mandatory headers (`SchemaValidationError`), negative prices, unparseable dates, and business rule logging. |
| `test_cleaner_transformer.py` | `DataCleaner` & `Transformer` | String whitespace stripping, uppercase normalization, `CustomerID = 'GUEST'` null imputation, duplicate dropping, and pre-computed date/feature accuracy. |
| `test_pipeline.py` | `ETLPipeline` | End-to-end execution flow, timing metrics tracking, `PipelineResult` generation, and controlled failure handling when validation fails. |
| `test_loader.py` | `DatabaseLoader` | Schema column mapping (`InvoiceNo` $\rightarrow$ `invoice_no`), chunked batch loading into in-memory SQLite, empty DataFrames, and transaction rollbacks. |
| `test_watermark.py` | `WatermarkManager` | SHA-256 file hash computation, duplicate file re-ingestion detection, and high-watermark datetime filtering. |
| `test_tracker.py` | `PipelineRunTracker` | Audit run lifecycle tracking (`RUNNING` $\rightarrow$ `SUCCESS` / `FAILED`), metric logging, and error message capture in `pipeline_runs`. |
| `test_lineage.py` | `DataLineageTracker` | Recording source file to target table mapping entries in `data_lineage` database table. |
| `test_quality_monitor.py` | `DataQualityMonitor` | Automated data quality percentage calculations, throughput metrics (`records_per_second`), and quality threshold status checks. |
| `test_spark_transformer.py` | `SparkDataTransformer` | Distributed PySpark transformation logic, Catalyst execution, and graceful fallback when Spark is absent. |
| `test_compute_router.py` | `ComputeRouter` | Dynamic routing between Pandas (<100MB) and PySpark ($\ge$100MB) based on file size thresholds. |
| `test_parquet_lake.py` | `ParquetDataLake` | Writing and reading Snappy-compressed Parquet files across raw, staged, and processed lake zones with `year=YYYY/month=MM` partitioning. |
| `test_storage.py` | `LocalStorageBackend` | File write, read, existence, and deletion methods on local filesystem storage. |
| `test_cloud_storage.py` | `CloudStorageBackend` | Mock cloud S3 object storage upload, download, list, and delete operations. |
| `test_database_pool.py` | `database/pool.py` | Engine pool creation, connection pre-ping validation, and database healthcheck assertions. |
| `test_cache.py` | `RedisCache` | Key GET/SET caching, TTL expiration, hit/miss metrics, and zero-downtime memory dictionary fallback. |
| `test_api.py` | `RetailLensAPI` | REST API endpoints (`/health`, `/ready`, `/metrics`, `/pipeline/runs`, `/analytics/kpis`) status codes and JSON schema outputs. |
| `test_metrics.py` | `PrometheusMetrics` | Incrementing counters, updating gauges, and rendering standard Prometheus exposition text format. |
| `test_orchestration.py` | `PipelineDAG` | DAG task dependency resolution, exponential backoff retries, fail-fast execution, and task concurrency locking. |
| `test_repository.py` | `AnalyticsRepository` | Parameterized SQL query generation, date filter boundaries, and empty query result DataFrames. |
| `test_kpi_engine.py` | `KPIEngine` & `Calculator` | Core, Sales, Customer, and Cancellation metric calculations and zero-division handling (`COALESCE`, `NULLIF`). |
| `test_insights.py` | `InsightEngine` | Threshold evaluation, `CRITICAL` cancellation alerts, MoM sales contraction warnings, and guest reliance insights. |
| `test_service.py` | `AnalyticsService` | Application service layer orchestration and executive summary data package construction. |
| `test_dashboard.py` | UI Formatters | Text, currency (`£`), number, percentage, and datetime formatting helper functions. |
| `test_sql_analytics.py` | `SQLAnalyticsService` | Execution of master SQL catalog queries (`queries.sql`) against in-memory database tables. |
| `test_kpis.py` | Scalar KPI Queries | Aggregation query output verification for total sales, order counts, AOV, and return rates. |
| `test_app_config.py` | `AppConfig` | Environment profile loading (`development` vs `production`), secret key verification, and `to_dict(mask_secrets=True)` redacting. |
| `test_logging_config.py` | `logging_config.py` | Log formatting, `RotatingFileHandler` creation, and `SensitiveDataFilter` credential masking. |
| `test_retry.py` | `execute_with_retry` | Retrying transient database network glitches with backoff while failing fast on permanent syntax errors. |
| `test_security.py` | Security Engine | Rejecting path traversal strings (`..`) in file inputs, parameterizing SQL statements, and enforcing 100MB file size limits. |
| `test_pipeline_monitor.py` | UI Page Monitor | Rendering pipeline monitoring dashboard UI components, health status badges, and run audit tables. |

---

## 13. CI/CD

Primary File: [`.github/workflows/ci.yml`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/.github/workflows/ci.yml)

### Continuous Integration Workflow (`ci.yml`)
RetailLens utilizes GitHub Actions for continuous integration. The workflow triggers on `push` and `pull_request` to `main` and `dev` branches:

```yaml
name: RetailLens Production CI/CD Pipeline

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

jobs:
  lint-and-test:
    name: Lint, Test & Validation Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
          cache: "pip"
      - name: Install Project Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run Full Unit & Integration Test Suite
        env:
          APP_ENV: testing
          LOG_LEVEL: WARNING
          STORAGE_BACKEND: local
        run: |
          python -m unittest discover tests -v

  docker-build:
    name: Container Build & Validation
    runs-on: ubuntu-latest
    needs: lint-and-test
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: retaillens:ci-latest
```

### Detailed Breakdown of Actual RetailLens CI Issue & Resolution

#### Problem
During automated CI workflow execution on GitHub Actions, `test_pipeline.py` failed with a breaking `TypeError: cannot unpack non-iterable ValidationReport object` and property access crashes on `report.passed_rows` / `report.failed_rows`.

#### Cause
1. **Return-Value Mismatch**: `DataValidator.validate(df)` was refactored to return a `Tuple[ValidationReport, pd.DataFrame]` so that flagged/type-casted DataFrames could pass to subsequent pipeline stages. However, legacy pipeline code and mock unit test fixtures still expected `validate()` to return a single `ValidationReport` object. When `ETLPipeline` attempted to unpack `report, df_valid = self.validator.validate(df_raw)`, calling it against older mock objects that returned a single `ValidationReport` instance caused Python to crash with a `TypeError`.
2. **Property Name Discrepancy**: Legacy test assertions inspected `report.passed_rows` and `report.failed_rows`, whereas the updated `ValidationReport` dataclass stored attributes as `valid_rows` and `invalid_rows`, causing `AttributeError` exceptions.

#### Fix
1. **Duck-Typing Inspection in `pipeline.py`**:
   `ETLPipeline` was updated to handle both return signatures dynamically:
   ```python
   val_output = self.validator.validate(df_raw)
   if isinstance(val_output, tuple):
       report, df_valid = val_output
   else:
       report = val_output
       df_valid = df_raw
   ```
2. **Alias Properties in `ValidationReport` Dataclass (`validator.py`)**:
   Properties were added to `ValidationReport` to maintain backwards compatibility with all test modules:
   ```python
   @property
   def passed_rows(self) -> int:
       """Alias for valid_rows metric."""
       return self.valid_rows

   @property
   def failed_rows(self) -> int:
       """Alias for invalid_rows metric."""
       return self.invalid_rows
   ```

#### Why the Fix Worked
* The duck-typing check allows `ETLPipeline` to accept both real `DataValidator` instances (which return a 2-element tuple) and lightweight test mocks (which return a single `ValidationReport`), eliminating unpack crashes.
* Adding `@property` aliases on `ValidationReport` seamlessly bridged legacy test assertions without breaking existing API contracts.
* The GitHub Actions CI pipeline passed 100% of the 77 unit tests across all 31 test modules.

---

## 14. Deployment

Primary Configurations: [`Dockerfile`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/Dockerfile), [`docker-compose.yml`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docker-compose.yml), [`deploy/kubernetes/`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/deploy/kubernetes/)

### Containerization Strategy (`Dockerfile`)
Multi-stage production build based on `python:3.10-slim`:
* **Stage 1 (Builder)**: Installs build tools (`gcc`, `g++`), compiles Python packages, and creates a clean wheel cache.
* **Stage 2 (Runtime)**: Copies only compiled dependencies into a lightweight slim image, reducing container image size by $70\%$.
* **Security Hardening**: Runs as a non-root user (`appuser` UID `10001`) with read-only root filesystem permissions.
* **Healthcheck Assertion**: Configures HTTP health check (`HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1`).

```dockerfile
FROM python:3.10-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.10-slim AS runtime
RUN useradd -u 10001 -m appuser
WORKDIR /app
COPY --from=builder /root/.local /home/appuser/.local
COPY . .
ENV PATH=/home/appuser/.local/bin:$PATH
USER 10001
EXPOSE 8501 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1
CMD ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Production Kubernetes Architecture (`deploy/kubernetes/`)
1. **`namespace.yaml`**: Isolates production workloads inside `retaillens-prod` namespace.
2. **`configmap.yaml`**: Injects non-sensitive environment configuration (`APP_ENV=production`, `LOG_LEVEL=INFO`, `STORAGE_BACKEND=cloud`, `PROCESSING_ENGINE=auto`).
3. **`secret.example.yaml`**: Mounts Base64-encoded production database credentials (`DATABASE_URL`) and Redis passwords securely into container pods.
4. **`deployment.yaml`**: Runs 2 load-balanced pod replicas running `retaillens:latest` with non-root security contexts, resource requests (`cpu: 250m`, `memory: 512Mi`), limits (`cpu: 1000m`, `memory: 2Gi`), Liveness probes (`GET /health`), and Readiness probes (`GET /ready`).
5. **`service.yaml`**: Exposes internal ClusterIP services on port 8501 (Streamlit UI) and port 8000 (REST API / Prometheus Metrics).
6. **`ingress.yaml`**: Configures NGINX Ingress Controller with TLS/SSL termination (`https://retaillens.analytics.com`).
7. **`hpa.yaml`**: Horizontal Pod Autoscaler automatically scales pod replicas from 2 up to 10 pods when CPU utilization exceeds $75\%$ or Memory exceeds $80\%$.

---

## 15. Challenges & Solutions

### 1. Non-UTF-8 Encoding Crashes
* **Problem**: Ingesting raw retail CSV exports containing non-ASCII symbols (e.g. `£` currency signs or accented customer names) threw `UnicodeDecodeError` and crashed the pipeline.
* **Cause**: Default `pd.read_csv()` assumes UTF-8 encoding, failing on `latin1` or `cp1252` files generated by legacy POS software.
* **Solution**: Implemented an automated multi-encoding fallback loop in `DataFileReader._read_csv_with_fallback()` (`utf-8` $\rightarrow$ `latin1` $\rightarrow$ `iso-8859-1` $\rightarrow$ `cp1252`).
* **Result**: $100\%$ ingestion resilience across all regional retail CSV exports without manual file conversion.

### 2. $25\%$ Sales Revenue Loss from Missing Customer IDs
* **Problem**: Over $25\%$ of total sales rows in raw datasets had missing `CustomerID` values. Running naive `dropna()` dropped those records.
* **Cause**: Guest checkouts in e-commerce platforms do not generate registered customer IDs.
* **Solution**: Implemented domain-specific null imputation in `DataCleaner`, replacing missing `CustomerID` values with `'GUEST'` and engineering a `CustomerType` classification (`'Guest'` vs `'Registered'`).
* **Result**: Preserved $100\%$ of company revenue metrics while supporting guest vs. registered customer cohort analysis.

### 3. Database Write Throughput Bottleneck
* **Problem**: Persisting processed datasets into PostgreSQL row-by-row in a Python loop achieved abysmal write speeds (~50 rows/sec), taking minutes to load moderate files.
* **Cause**: Inserting rows one-by-one incurs a separate network TCP round-trip and transaction overhead for every row.
* **Solution**: Implemented chunked multi-row batch inserts in `DatabaseLoader` (`df.to_sql(chunksize=1000, method="multi")`) wrapped in an atomic SQLAlchemy transaction block (`with engine.begin():`).
* **Result**: Increased database write throughput by over **50x** (~2,500+ rows/sec) while guaranteeing ACID atomicity via auto-rollback on error.

### 4. Single-Node RAM Memory Exhaustion (OOM)
* **Problem**: Processing raw tabular datasets exceeding 2GB on single-node environments saturated system RAM, triggering Out-of-Memory container crashes.
* **Cause**: Pandas requires contiguous memory in RAM, consuming 5x–10x dataset file size during transformations.
* **Solution**: Built a `ComputeRouter` module that evaluates dataset file size against a threshold (`100`MB). Small files route to Pandas, while large datasets ($\ge 100$MB) route to `SparkDataTransformer` for distributed PySpark execution.
* **Result**: Zero OOM crashes; seamlessly scales from small local files up to multi-gigabyte big data workloads.

### 5. CI Test Unpack Crash on Validation Engine Refactor
* **Problem**: GitHub Actions CI workflow failed with `TypeError: cannot unpack non-iterable ValidationReport object`.
* **Cause**: `DataValidator.validate()` was updated to return `Tuple[ValidationReport, pd.DataFrame]`, but legacy test mocks still returned a single `ValidationReport` object.
* **Solution**: Added duck-typing result checking in `ETLPipeline` (`if isinstance(val_output, tuple): report, df = val_output else: report = val_output`) and added `@property` aliases (`passed_rows`, `failed_rows`) to `ValidationReport`.
* **Result**: CI pipeline passed $100\%$ of unit and integration tests across 31 test modules.

---

## 16. Important Design Decisions

| Architectural Decision | Option Selected | Why Selected | Alternatives Considered | Why Alternatives Were Not Chosen | When Alternative Would Be Better |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Architecture** | **Modular Decoupled Design** | Isolates responsibilities into `ingestion/`, `database/`, `analytics/`, `app/` so UI changes don't break database logic. | Monolithic single-script architecture | Monolithic scripts become unmaintainable and impossible to unit-test as codebases grow. | Quick 50-line exploratory Jupyter notebook prototypes. |
| **Compute Engine** | **Hybrid Router (Pandas + PySpark)** | Combines zero-overhead execution for small files (<100MB) with PySpark Catalyst cluster scaling for big data ($\ge$100MB). | PySpark Only / Pandas Only | PySpark adds unnecessary JVM startup latency for small files; Pandas crashes on multi-GB datasets. | Dedicated big data lakehouses where all files exceed 50GB. |
| **Database System** | **Managed Cloud PostgreSQL** | Production ACID-compliant relational warehouse with B-Tree indexes, CTEs, window functions, and connection pooling. | SQLite / MongoDB | SQLite lacks cloud concurrency; MongoDB lacks native relational joins for complex analytics. | SQLite for lightweight offline desktop apps; MongoDB for unstructured log documents. |
| **Ingestion Gate** | **Validation Firewall Before Loading** | Enforces fail-fast schema checks and soft quality audits before corrupt data pollutes database storage. | Direct load without validation | Loading raw un-validated data leads to silent table corruption and broken downstream queries. | High-speed IoT telemetry ingestion into raw staging data lakes. |
| **Null Imputation** | **Impute `CustomerID = 'GUEST'`** | Preserves $25\%$ of company sales revenue data from guest checkouts while supporting cohort filtering. | `df.dropna(subset=['CustomerID'])` | Indiscriminately dropping null customer IDs deletes valid sales transactions, warping revenue KPIs. | Machine learning churn models requiring strict individual user tracking. |
| **Analytics Engine** | **Database SQL Aggregation** | PostgreSQL computes aggregates (`SUM`, `COUNT`, `AOV`) directly in DB, returning bytes over network. | In-memory Pandas UI aggregation | Pulling 500,000 raw rows into Pandas memory saturates network bandwidth and web server RAM. | Complex non-SQL machine learning model feature matrix training. |
| **Caching Layer** | **Redis with Memory Fallback** | Key TTL caching accelerates query responses with zero downtime if Redis partition occurs. | No Caching / Streamlit Cache Only | Un-cached queries hit PostgreSQL repeatedly; Streamlit cache is limited to single web container RAM. | Ultra-low-latency real-time trading systems requiring microsecond freshness. |
| **Deployment Target** | **Kubernetes + Multi-Stage Docker** | Declarative scaling, self-healing pod restarts, TLS ingress, and zero-downtime rolling updates. | Bare-Metal VM / Heroku | Bare-metal lacks automated autoscaling; Heroku lacks fine-grained container security controls. | Lightweight static internal dashboards with minimal traffic. |

---

## 17. Complete End-to-End Example

### Step-by-Step Execution Trace of a Retail Data File

```text
Incoming File: data/raw/online_retail_2010.csv (Size: 45 MB)
```

1. **User Upload / Trigger**: File is placed in `data/raw/online_retail_2010.csv` or uploaded via Streamlit UI.
2. **Ingestion Entry (`DataFileReader`)**:
   * Inspects metadata: Checks path exists, extension `.csv` is allowed, and size ($45$MB) $< 100$MB guardrail limit.
   * Execution: Calls `_read_csv_with_fallback()`. Attempts UTF-8; if a currency symbol `£` triggers `UnicodeDecodeError`, it falls back to `latin1` and parses 541,909 raw rows into a DataFrame.
3. **Hybrid Compute Router (`ComputeRouter`)**:
   * Evaluates size ($45\text{ MB} < 100\text{ MB}$). Selects **Pandas Execution Engine** for zero-overhead performance.
4. **Data Quality Firewall (`DataValidator`)**:
   * Asserts header presence (`InvoiceNo`, `StockCode`, `Quantity`, `InvoiceDate`, `UnitPrice`).
   * Validates numeric types and parses datetimes.
   * Generates a `ValidationReport`: Identifies 535,187 valid rows and 6,722 soft anomaly rows (negative return quantities logged, zero invalid hard schema errors).
5. **Data Cleaning (`DataCleaner`)**:
   * Trims whitespace on string columns. Converts `StockCode` to uppercase.
   * Imputes missing `CustomerID` values ($135,080$ nulls) to `'GUEST'`.
   * Filters invalid negative prices and drops 5,268 exact duplicate composite records.
6. **Feature Pre-computation (`DataTransformer`)**:
   * Calculates `TotalPrice = Quantity * UnitPrice`.
   * Extracts date attributes: `InvoiceYear = 2010`, `InvoiceMonth = 12`, `InvoiceWeekday = 'Wednesday'`, `InvoiceHour = 8`.
   * Flags `IsCancellation = True` for return orders (`Quantity < 0`).
   * Assigns `CustomerType = 'Guest'` and `RevenueBucket = 'Medium (£10-£50)'`.
7. **Parquet Data Lake Persistence (`ParquetDataLake`)**:
   * Writes Snappy-compressed Parquet file to `data/processed/year=2010/month=12/processed_online_retail_2010.parquet`.
8. **Idempotent Database Load (`DatabaseLoader`)**:
   * Maps DataFrame feature names to PostgreSQL DDL schema (`COLUMN_MAPPING`).
   * Queries existing natural keys `(invoice_no, stock_code, invoice_timestamp)` to execute a left anti-join filter, preventing duplicate insertion.
   * Opens atomic transaction block (`with engine.begin() as conn:`).
   * Executes chunked multi-row batch insert (`chunksize=1000`, `method="multi"`) into PostgreSQL table `fact_sales`.
   * Automatically commits 529,919 clean rows into Neon Cloud PostgreSQL.
9. **Audit & Lineage Recording (`PipelineRunTracker` & `DataLineageTracker`)**:
   * Inserts execution audit log into `pipeline_runs` (`status="SUCCESS"`, `duration_seconds=14.2`, `rows_inserted=529919`).
   * Inserts lineage map into `data_lineage` linking `online_retail_2010.csv` to `fact_sales`.
10. **Analytics & Dashboard Render (`SQLAnalyticsService` & Streamlit)**:
    * User opens Streamlit dashboard.
    * `SQLAnalyticsService` queries PostgreSQL database: `SUM(total_amount)` returns Total Revenue ($\$9,747,747.93$), AOV ($\$479.49$), and Cancellation Rate ($1.84\%$).
    * `InsightEngine` evaluates metrics and generates an `INFO` insight card: *"Revenue healthy; Guest checkout accounts for 20.3% of monthly spend."*
    * Plotly renders monthly sales trend line and product leaderboard charts in the browser.

---

## 18. Important Files & Functions

### 1. `config/schema_config.py`
* **Purpose**: Central configuration defining data contracts, schema rules, and ingestion guardrails.
* **Key Class**: `IngestionConfig`
* **Dependencies**: None (pure Python standard library).
* **Where It Fits**: Config layer providing schema contracts to `reader.py` and `validator.py`.
* **Interview Point**: *"Centralizing schema contracts prevents hardcoding string column names inside business logic."*

### 2. `ingestion/reader.py`
* **Purpose**: Defensive file ingestion reader handling guardrails and encoding resilience.
* **Key Class**: `DataFileReader`
* **Important Functions**: `validate_file_metadata()`, `_read_csv_with_fallback()`, `read_file()`
* **Input**: Raw file path (`str`). **Output**: Pandas DataFrame (`pd.DataFrame`).
* **Dependencies**: `pandas`, `config.schema_config.IngestionConfig`
* **Where It Fits**: Entry point boundary of the ETL pipeline.
* **Interview Point**: *"Pre-checks file size (<100MB) to prevent OOM attacks and uses multi-encoding fallback (UTF-8 -> Latin1) to stop decoding crashes."*

### 3. `ingestion/validator.py`
* **Purpose**: Data Quality Firewall inspecting schema structures and reporting business rule anomalies.
* **Key Classes**: `DataValidator`, `ValidationReport`, `SchemaValidationError`
* **Important Functions**: `validate()`, `_validate_schema_structure()`, `_validate_business_rules()`
* **Input**: Raw DataFrame. **Output**: `Tuple[ValidationReport, pd.DataFrame]`
* **Dependencies**: `pandas`, `dataclasses`
* **Where It Fits**: Quality control checkpoint between reading and cleaning.
* **Interview Point**: *"Separates hard fail-fast structural schema errors from soft business rule anomalies captured in ValidationReport."*

### 4. `ingestion/cleaner.py`
* **Purpose**: Vectorized sanitization, null value imputation, and row deduplication.
* **Key Class**: `DataCleaner`
* **Important Functions**: `clean()`, `_sanitize_strings()`, `_impute_missing_values()`, `_remove_duplicates()`
* **Input**: Validated DataFrame. **Output**: Sanitized clean DataFrame.
* **Dependencies**: `pandas`, `numpy`
* **Where It Fits**: Data sanitization stage of ETL pipeline.
* **Interview Point**: *"Imputes missing CustomerID to 'GUEST' instead of dropping rows, preserving 25% of company revenue data."*

### 5. `ingestion/transformer.py`
* **Purpose**: Feature engineering and pre-computation of temporal attributes and spend categories.
* **Key Class**: `DataTransformer`
* **Important Functions**: `transform()`, `_compute_total_price()`, `_extract_temporal_features()`, `_bin_revenue_buckets()`
* **Input**: Clean DataFrame. **Output**: Enriched transformed DataFrame.
* **Dependencies**: `pandas`, `numpy`
* **Where It Fits**: Data enrichment stage before persistence.
* **Interview Point**: *"Pre-calculating features during ETL speeds up downstream SQL queries and Streamlit charts by 10x."*

### 6. `ingestion/pipeline.py`
* **Purpose**: Decoupled orchestrator coordinating ETL stages, timing metrics, and error logging.
* **Key Classes**: `ETLPipeline`, `PipelineConfig`, `PipelineResult`
* **Important Function**: `run(file_path)`
* **Input**: Dataset file path. **Output**: `PipelineResult` dataclass.
* **Dependencies**: `reader`, `validator`, `cleaner`, `transformer`, `loader`, `watermark`, `tracker`
* **Where It Fits**: Core execution engine of the ingestion pipeline.
* **Interview Point**: *"Enforces SOLID principles and Dependency Injection, allowing mock stage replacement during unit testing."*

### 7. `ingestion/loader.py`
* **Purpose**: Persistence engine executing anti-join deduplication and multi-row batch inserts into PostgreSQL.
* **Key Class**: `DatabaseLoader`
* **Important Functions**: `load()`, `_column_mapping()`, `_anti_join_deduplicate()`
* **Input**: Transformed DataFrame & target table name. **Output**: `LoadResult` dataclass.
* **Dependencies**: `sqlalchemy`, `database.pool.create_pooled_engine`
* **Where It Fits**: Persistence layer writing to PostgreSQL warehouse.
* **Interview Point**: *"Uses chunked multi-row batch inserts (chunksize=1000) inside atomic transaction blocks for 50x faster write throughput."*

### 8. `database/pool.py`
* **Purpose**: Database connection pool management and pre-ping healthcheck validation.
* **Important Functions**: `create_pooled_engine()`, `check_db_health()`
* **Input**: DB connection string. **Output**: SQLAlchemy `Engine` instance.
* **Dependencies**: `sqlalchemy`
* **Where It Fits**: Database connectivity foundation layer.
* **Interview Point**: *"Configures pool_size=10 and pool_pre_ping=True to reuse database sockets and prevent stale connection crashes."*

### 9. `analytics/service.py`
* **Purpose**: Application service layer compositing repository queries, KPI engines, and insight generators.
* **Key Class**: `AnalyticsService`
* **Important Functions**: `get_executive_summary()`, `get_sales_trends()`, `get_product_performance()`
* **Input**: Filter boundary parameters. **Output**: Formatted summary dictionaries for UI.
* **Dependencies**: `AnalyticsRepository`, `KPIEngine`, `InsightEngine`
* **Where It Fits**: Backend API service layer powering Streamlit UI and REST endpoints.
* **Interview Point**: *"Decouples UI views from database queries, providing a clean zero-SQL boundary for frontend developers."*

### 10. `api/app.py`
* **Purpose**: Production REST API boundary exposing endpoints for external clients and K8s probes.
* **Key Class**: `RetailLensAPI`
* **Important Endpoints**: `GET /health`, `GET /ready`, `GET /metrics`, `GET /pipeline/runs`, `GET /analytics/kpis`
* **Dependencies**: `fastapi` / `Flask`, `AnalyticsService`, `PrometheusMetricsExporter`
* **Where It Fits**: System boundary exposing REST HTTP APIs.
* **Interview Point**: *"Provides Liveness and Readiness HTTP probes for Kubernetes pod traffic routing."*

---

## 19. Important Technical Concepts

### 1. ETL vs. ELT
* **ETL (Extract, Transform, Load - RetailLens)**: Data is transformed *before* loading into target database storage. Ideal for protecting database storage from un-sanitized data and enforcing schema quality.
* **ELT (Extract, Load, Transform)**: Raw data is loaded directly into scalable cloud data warehouses (Snowflake/BigQuery) and transformed inside the warehouse using SQL (dbt).

### 2. OLTP vs. OLAP
* **OLTP (Online Transaction Processing - PostgreSQL)**: Row-oriented database storage optimized for fast, transactional write operations, row lookups, and ACID compliance.
* **OLAP (Online Analytical Processing - Snowflake/BigQuery)**: Column-oriented storage optimized for reading specific columns across millions of rows during heavy analytical aggregation queries.

### 3. Dimensional Data Modeling (Star Schema)
* **Fact Table (`fact_sales`)**: Central table containing numerical business metrics (quantity, unit price, total amount).
* **Dimension Tables (`dim_customer`, `dim_product`)**: Contextual tables containing descriptive text attributes (customer country, product category).
* **Surrogate Key vs. Natural Key**: Surrogate keys are system-generated auto-increment integers (`transaction_id`); natural keys are operational identifiers (`invoice_no`, `stock_code`).

### 4. B-Tree Database Indexing
A balanced search tree index structure maintained on disk by PostgreSQL. Reduces search time complexity from $O(N)$ full table scans down to $O(\log N)$ index lookups for high-cardinality columns.

### 5. Idempotency & Watermarking
* **Idempotency**: Executing an operation multiple times produces the exact same result without unintended side effects (e.g. avoiding duplicate row creation on pipeline re-runs).
* **High Watermark**: Tracking the maximum processed timestamp (`MAX(invoice_timestamp)`) or file SHA-256 hash to filter out previously ingested records.

### 6. Connection Pooling
Maintaining a persistent pool of reusable database socket connections (`pool_size=10`). Eliminates TCP handshake latency and socket setup overhead on every query.

### 7. Circuit Breakers & Exponential Backoff
* **Exponential Backoff**: Retrying failed operations with exponentially increasing wait delays ($0.1\text{s} \rightarrow 0.2\text{s} \rightarrow 0.4\text{s}$) to avoid overwhelming recovering cloud services.
* **Circuit Breaker**: Temporarily halting calls to a failing external service to prevent cascading system failures.

---

## 20. Interview Questions & Answers

### Topic 1: Software Engineering & Architecture

#### Q1: What is modular architecture, and how is it implemented in RetailLens?
* **Answer**: Modular architecture decomposes an application into independent, self-contained modules—each responsible for a single business capability. In RetailLens, we isolate concerns across distinct directories: `ingestion/` reads and validates files, `database/` manages connection pools and SQL DDLs, `analytics/` calculates business KPIs, and `app/` controls Streamlit UI layouts. This ensures high cohesion within modules and loose coupling between modules, allowing frontend updates without risking database breakage.

#### Q2: How does Dependency Injection improve testability in your pipeline?
* **Answer**: Dependency Injection passes dependent stage handlers (`reader`, `validator`, `cleaner`, `loader`) into the `ETLPipeline` constructor rather than instantiating them internally. During unit testing in `tests/test_pipeline.py`, we inject mock stage objects to test flow control, execution timing, and error handling without performing real disk file I/O or connecting to live databases.

---

### Topic 2: Data Ingestion & Quality Validation

#### Q3: How do you handle encoding issues when reading raw CSV files in production?
* **Answer**: Legacy retail POS exports often contain non-UTF-8 characters (e.g. `£` currency signs or accented customer names) encoded in `latin1` or `cp1252`. We implement an automated encoding fallback loop in `DataFileReader._read_csv_with_fallback()`: the reader attempts parsing with `utf-8`; if a `UnicodeDecodeError` is caught, it sequentially retries `latin1`, `iso-8859-1`, and `cp1252` before failing.

#### Q4: Why impute missing `CustomerID` as `'GUEST'` instead of dropping missing rows?
* **Answer**: In retail datasets, missing customer IDs represent guest checkouts rather than corrupted data. Indiscriminately running `df.dropna(subset=['CustomerID'])` discards $25\%$ of total sales revenue data, warping revenue KPIs. Imputing `CustomerID = 'GUEST'` preserves total revenue metrics while allowing customer analytics queries to easily filter between guest and registered customer cohorts.

#### Q5: What is the difference between hard schema validation errors and soft business rule validation errors?
* **Answer**: Hard structural schema errors (empty DataFrame, duplicate headers, missing required columns like `Quantity`) make parsing impossible and raise `SchemaValidationError` immediately (**fail-fast strategy**). Soft business rule errors (negative unit price, unparseable date) represent row-level anomalies; these are recorded in a `ValidationReport` dataclass without crashing the pipeline, allowing valid rows to proceed.

---

### Topic 3: Database & SQL Performance

#### Q6: How does `DatabaseLoader` achieve a 50x improvement in database write throughput?
* **Answer**: Inserting database records row-by-row in a Python loop incurs a separate network TCP round-trip for every row (~50 rows/sec). `DatabaseLoader` executes chunked multi-row batch inserts (`df.to_sql(chunksize=1000, method="multi")`), grouping 1,000 rows into single SQL statements to increase write throughput to over 2,500+ rows/sec.

#### Q7: How do you guarantee database ACID atomicity during load failures?
* **Answer**: We wrap bulk database loads inside an explicit SQLAlchemy transaction context block (`with self.engine.begin() as conn:`). Under ACID properties, Atomicity guarantees an all-or-nothing operation: if a batch insertion fails midway due to a network glitch, SQLAlchemy automatically executes a database `ROLLBACK`, restoring PostgreSQL to its exact pre-load state.

#### Q8: Explain the difference between `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()`.
* **Answer**: For tied values (e.g., two customers with identical $1,000 spend):
  * `ROW_NUMBER()` assigns unique sequential integers arbitrarily (1, 2, 3).
  * `RANK()` assigns identical ranks with gaps (1, 1, 3).
  * `DENSE_RANK()` assigns identical ranks without gaps (1, 1, 2).

---

### Topic 4: CI/CD & Deployment

#### Q9: What was the DataValidator return-value mismatch CI issue, and how was it resolved?
* **Answer**: `DataValidator.validate()` was updated to return a 2-element tuple `(ValidationReport, DataFrame)`, but legacy test mocks still returned a single `ValidationReport` object, causing `TypeError: cannot unpack non-iterable ValidationReport object` during GitHub Actions CI runs. We resolved this by adding duck-typing result checking in `ETLPipeline` (`if isinstance(val_output, tuple): report, df = val_output else: report = val_output`) and adding `@property` aliases (`passed_rows`, `failed_rows`) to `ValidationReport`.

#### Q10: How do Liveness and Readiness probes differ in Kubernetes?
* **Answer**: A **Liveness Probe** (`GET /health`) checks if the container process is alive; if it fails, Kubernetes restarts the pod container. A **Readiness Probe** (`GET /ready`) checks if the pod is ready to accept user traffic by verifying database connection pool health; if it fails, Kubernetes removes the pod IP from load balancer endpoints without restarting it.

---

## 21. Project Explanation

### ⏱️ 30-Second Pitch (Recruiters & Screening Calls)
> *"RetailLens is an enterprise-grade retail analytics platform I built using Python, PySpark, PostgreSQL, Streamlit, Docker, and Kubernetes. It automates the ingestion of messy e-commerce transaction datasets, runs a defensive data quality firewall, executes a hybrid compute ETL pipeline routing between Pandas and Spark, stores data in a cloud PostgreSQL data warehouse, and presents interactive visual business analytics via Streamlit."*

---

### ⏱️ 1-Minute Pitch (Technical Screening & Hiring Managers)
> *"In RetailLens, I architected a modular Data Ingestion & Analytics platform using Python, PySpark, SQLAlchemy, Neon Cloud PostgreSQL, and Streamlit.
> 
> The pipeline features a defensive file reader that enforces 100MB file limits and multi-encoding fallbacks (`utf-8`, `latin1`, `cp1252`) to eliminate parsing crashes. Our data quality firewall separates hard structural schema errors from soft business rule anomalies, capturing error metrics in a `ValidationReport`. 
> 
> The cleaner sanitizes text and imputes missing customer IDs as `'GUEST'`, preserving 25% of valid sales revenue. To scale, our `ComputeRouter` routes small files (<100MB) to Pandas and big data datasets to distributed PySpark. 
> 
> Persistence uses SQLAlchemy connection pooling and chunked multi-row batch inserts (`chunksize=1000`) inside atomic transaction blocks for 50x faster write throughput. Finally, we expose analytics via a Streamlit BI dashboard, production REST API, and Prometheus metrics exporter."*

---

### ⏱️ 2–3 Minute Detailed Pitch (Senior Technical Leads & System Design Rounds)
> *"I'd love to walk you through the architecture and engineering trade-offs of RetailLens.
> 
> **1. Problem & Ingestion Boundary**: RetailLens processes raw retail sales datasets exported from heterogeneous POS systems. To protect server RAM against Out-of-Memory crashes, `DataFileReader` validates metadata (file size <100MB and extension) before parsing. To handle legacy POS exports with currency symbols (`£`), we implement an automated multi-encoding fallback loop (`utf-8` -> `latin1` -> `cp1252`) that catches decoding exceptions silently.
> 
> **2. Quality Firewall & Cleaning**: `DataValidator` acts as a Data Quality Firewall. Hard structural schema errors throw a `SchemaValidationError` immediately (fail-fast), while soft business rule anomalies populate a `ValidationReport` dataclass. In `DataCleaner`, we chose domain imputation over naive deletion: missing customer IDs represent guest checkouts; imputing `'GUEST'` preserves 25% of company sales data while supporting customer cohort analysis.
> 
> **3. Hybrid Compute & Feature Engineering**: To handle scalability, `ComputeRouter` dynamically evaluates file size: datasets under 100MB run on Pandas for low latency, while datasets over 100MB route to `SparkDataTransformer` for distributed PySpark execution. Pre-computing features (`TotalPrice`, date attributes, `RevenueBucket`) during ETL speeds up downstream SQL queries and dashboard loads by 10x.
> 
> **4. Persistence & Reliability**: `DatabaseLoader` maps features to our PostgreSQL schema and executes chunked multi-row batch inserts (`chunksize=1000`, `method="multi"`) inside an atomic `with engine.begin():` transaction block, yielding 50x faster write throughput with automatic rollback protection. Database connections use SQLAlchemy engine pooling (`pool_size=10`, `pool_pre_ping=True`).
> 
> **5. Observability & Deployment**: The system exposes a REST API boundary, Redis cache with memory fallback, Prometheus metrics exporter, and Streamlit BI web app. Deployment is containerized using a 2-stage non-root `Dockerfile` and automated via GitHub Actions CI and production Kubernetes manifests with HPA autoscaling."*

---

## 22. Last-Minute Revision

### ⚡ Quick-Reference Flashcards for Interview Prep

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             RETAILLENS AT A GLANCE                               │
└──────────────────────────────────────────────────────────────────────────────────┘
• Purpose: End-to-end retail analytics platform, data quality firewall & distributed ETL engine.
• Tech Stack: Python 3.10, Pandas, PySpark, PostgreSQL (Neon), SQLAlchemy, Streamlit, Plotly, Docker, Kubernetes, Prometheus, Redis, GitHub Actions.
• Key Architecture: Raw File ──► Reader ──► Validator ──► Router (Pandas/Spark) ──► Cleaner ──► Transformer ──► Parquet Lake ──► PostgreSQL ──► Analytics Service ──► Streamlit / REST API.
• File Size Guardrail: 100 MB max limit (`MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024`).
• Encoding Fallback Order: ["utf-8", "latin1", "iso-8859-1", "cp1252"].
• Imputation Rule: `CustomerID = 'GUEST'` (Preserves 25% of revenue data from guest checkouts).
• Pre-Computed Features: TotalPrice (`Quantity * UnitPrice`), InvoiceYear, InvoiceMonth, InvoiceQuarter, InvoiceWeekday, InvoiceHour, IsCancellation, CustomerType, RevenueBucket.
• Database Target Table: `fact_sales` (Primary Key: `transaction_id BIGSERIAL`).
• DB Indexes: B-Tree indexes on `invoice_no`, `customer_id`, `stock_code`, `invoice_timestamp`, `country`, and composite `(invoice_year, invoice_month)`.
• Connection Pool Config: `pool_size=10`, `max_overflow=20`, `pool_timeout=30`, `pool_recycle=1800`, `pool_pre_ping=True`.
• DB Batch Load Config: `df.to_sql(chunksize=1000, method="multi")` inside `with engine.begin():` context block (50x write throughput boost).
• Scalability Router: Files < 100MB ──► Single-Node Pandas | Files >= 100MB ──► Distributed PySpark.
• Data Lake Format: Snappy-compressed Parquet partitioned by `year=YYYY/month=MM`.
• Key SQL Formulas:
  - AOV: `ROUND(SUM(total_amount) / NULLIF(COUNT(DISTINCT invoice_no), 0), 2)`
  - Return Rate %: `ROUND((COUNT(DISTINCT CASE WHEN is_cancellation = TRUE THEN invoice_no END)::NUMERIC / NULLIF(COUNT(DISTINCT invoice_no), 0)) * 100, 2)`
  - MoM Growth: `((current_rev - LAG(current_rev) OVER (...)) / NULLIF(LAG(current_rev) OVER (...), 0)) * 100`
• CI Issue Fix: Checked `val_output` duck-typing in `pipeline.py` (`isinstance(val_output, tuple)`) and added `@property` aliases (`passed_rows`, `failed_rows`) to `ValidationReport`.
• Container Security: Multi-stage `Dockerfile`, non-root user `appuser` (UID `10001`), HTTP healthchecks.
• K8s Probes: Liveness Probe (`GET /health`), Readiness Probe (`GET /ready`).
• Test Suite: 31 test modules, 77 unit & integration tests (`python -m unittest discover tests -v`).
```
