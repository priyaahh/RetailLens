# 📖 Phase 1 Learning Summary & Architectural Rationale

This document serves as your long-term study guide, technical revision note, and architectural decision record (ADR) for **Phase 1: Project Initialization & Architecture Design**.

---

## 1. 💡 Phase 1 Learning Summary

### Architecture
RetailLens is built with a **decoupled, modular architecture**. Ingestion (`app/` & `etl/`), storage (`database/`), analytics (`analytics/`), and visualization (`dashboard/` & `reports/`) operate in isolated modules. This ensures changes to the frontend do not break database operations, and database schema updates do not crash the ETL pipeline.

### Folder Structure
* `app/`: Streamlit web app UI & page layout code.
* `data/`: In-memory storage subdirectories (`raw/`, `processed/`, `archive/`). `.gitkeep` ensures git tracks folder hierarchy while ignoring data files.
* `etl/`: Ingestion, quality validation, transformation, and database loading modules.
* `database/`: Database connection management, DDL schema definitions, and SQL analytics scripts.
* `analytics/`: Business metric calculations, insight algorithms, and machine learning forecasting models.
* `dashboard/`: Custom Plotly charting helper functions.
* `reports/`: Power BI desktop report files (.pbix) and static export artifacts.
* `logs/`: Application execution logs for debugging and auditability.
* `docs/`: Technical notes, interview preparation guides, and revision records.

### Git & Source Control
We utilize **Git** with GitHub hosting. Code is organized using feature branches (`feature/etl`, `feature/database`, etc.) merging into `main`. `.gitignore` excludes virtual environments (`.venv/`), raw data dumps (`data/raw/*`), runtime logs (`logs/*.log`), and secret files (`.env`).

### Virtual Environments (`.venv`)
A virtual environment isolates project dependencies from the global system Python installation. It prevents dependency version conflicts across multiple Python projects on the same machine.

### Environment Variables (`.env` & `.env.example`)
Application secrets (database credentials, passwords, ports) are stored in a `.env` file and accessed via `python-dotenv`. `.env` is excluded from Git to prevent secret leaks. `.env.example` is committed as a template for team developers and deployment services.

### End-to-End Workflow
1. User uploads CSV/Excel file in Streamlit.
2. Data quality engine checks schema, missing values, duplicates, and invalid data types.
3. Cleaned data is transformed, feature-engineered, and staging-archived.
4. Processed data is loaded into Neon PostgreSQL via SQLAlchemy.
5. Analytical metrics and ML sales forecasts are computed.
6. Insights are presented dynamically in Streamlit and exported to Power BI dashboards.

### PostgreSQL
A managed relational database engine (Neon PostgreSQL) hosting structured fact tables. It supports ACID transactions, schema constraints, primary/foreign keys, and complex ANSI SQL query processing.

### Streamlit
A pure-Python web framework that converts Python scripts into interactive, reactive web applications without requiring separate HTML/CSS/JavaScript codebases.

### Power BI
An enterprise Business Intelligence platform used to create interactive visual dashboards and reports for C-suite executive stakeholders.

### ETL Overview
* **Extract**: Ingestion of raw tabular files (CSV/Excel).
* **Transform (Validate + Clean)**: Data quality checking, missing value imputation, type casting, and feature engineering.
* **Load**: Bulk insertion into PostgreSQL database tables.

### Deployment Overview
The application code is pushed to GitHub and deployed publicly on **Streamlit Community Cloud**, connecting securely to the **Neon Cloud PostgreSQL** instance over encrypted TLS/SSL.

---

## 2. 🎯 The "Why" Architectural Decision Record (ADR)

| Decision Category | Decision Made | Why We Made It | Alternatives Considered | Why Alternatives Were Not Chosen | When Alternatives Would Be Better |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Language** | **Python** | Unified ecosystem for Data Engineering, Pandas, Machine Learning, and Streamlit UI. | Java / Go | Higher boilerplate code, steeper learning curve, less seamless integration with data science libraries. | Building high-throughput microservices requiring microsecond execution latencies. |
| **Data Engine** | **Pandas** | In-memory tabular manipulation ideal for dataset sizes under 2GB. | PySpark / Polars | PySpark requires JVM cluster management; Polars introduces non-standard syntax for beginners. | Datasets exceeding single-node RAM memory limits (>10GB+ to Terabytes). |
| **Database** | **Managed PostgreSQL** | Robust relational model, full ANSI SQL support, CTEs, and window functions. | MongoDB / SQLite | MongoDB lacks relational joins; SQLite is local file-based and unsuitable for cloud deployments. | MongoDB for un-structured document logs; SQLite for lightweight embedded desktop apps. |
| **Database ORM** | **SQLAlchemy** | Connection pooling, SQL injection prevention, dialect abstraction, and seamless Pandas integration (`to_sql`). | Raw `psycopg2` | Raw SQL string concatenation creates security risks and manual connection management overhead. | Simple single-query scripts without ORM overhead. |
| **Frontend UI** | **Streamlit** | Rapid creation of web applications directly in Python without frontend frameworks. | React + FastAPI | React requires JavaScript, HTML/CSS, build tooling, and API endpoint state synchronization. | Enterprise SaaS applications requiring custom design systems, animations, and micro-frontends. |
| **Visualizations** | **Plotly** | Interactive JavaScript charts inside browser with tooltips, panning, and zooming. | Matplotlib / Seaborn | Matplotlib renders static PNG images, losing interactive user exploration capabilities. | Generating static PDF research reports or inline print visualizations. |
| **BI Reporting** | **Power BI** | Industry standard in enterprise retail for executive executive dashboards. | Tableau | Tableau has restrictive free tier options for individual portfolio projects. | Enterprise organizations strictly standardized on the Salesforce/Tableau stack. |
| **Cloud Hosting** | **Neon PostgreSQL** | Zero-cost serverless PostgreSQL with native SSL security and connection pooling. | AWS RDS PostgreSQL | AWS RDS free tier requires credit cards and can incur accidental charges if misconfigured. | High-traffic enterprise databases requiring dedicated compute nodes and multi-region read replicas. |
| **Git Strategy** | **Feature Branches** | Isolates feature development without risking code breaks on `main`. | GitFlow (`dev`, `staging`) | GitFlow adds unnecessary branching overhead for a single-developer project. | Multi-developer engineering teams managing concurrent release cycles and hotfixes. |

---

## 3. ⚠️ Common Setup Mistakes & How RetailLens Avoids Them

1. **Hardcoding DB Credentials in Code**:
   * *Mistake*: Placing DB passwords inside `database/connection.py`.
   * *RetailLens Fix*: Uses `.env` and `python-dotenv` to inject environment variables securely at runtime. `.env` is added to `.gitignore`.

2. **Committing Virtual Environments & Raw Data Files**:
   * *Mistake*: Uploading `.venv/` (hundreds of MBs of packages) or raw CSV files to GitHub.
   * *RetailLens Fix*: Explicitly configures `.gitignore` rules to exclude virtual environments, raw data dumps, and log files.

3. **Mixing Database Logic in Frontend UI Views**:
   * *Mistake*: Writing raw SQL queries directly inside Streamlit UI page files.
   * *RetailLens Fix*: Separates query logic into `database/queries.sql`, connection logic into `database/connection.py`, and UI into `app/`.

4. **Installing Dependencies Globally**:
   * *Mistake*: Running `pip install pandas` globally in system Python, leading to version conflicts.
   * *RetailLens Fix*: Enforces project isolation using a virtual environment (`python -m venv .venv`).

5. **Not Pinning Library Dependency Versions**:
   * *Mistake*: Using empty `requirements.txt` which installs major version updates that break breaking changes.
   * *RetailLens Fix*: Defines baseline version bounds in `requirements.txt` (e.g., `pandas>=2.0.0`).

---

## ⚡ 5-Minute Technical Interview Cheat Sheet

### Essential Terminal Commands
```bash
# Environment Setup
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt

# Git Feature Workflow
git checkout main
git checkout -b feature/etl
git add etl/
git commit -m "feat(etl): add schema validation engine"
git checkout main
git merge feature/etl
```

### Key Terminology
* **ETL**: Extract (read raw file), Transform (validate, clean, engineer features), Load (write to PostgreSQL).
* **OLTP vs. OLAP**: PostgreSQL is row-oriented OLTP (ACID, transactional); Snowflake/BigQuery is column-oriented OLAP (massive analytical aggregation).
* **Decoupled Architecture**: Separating data processing, storage, analytics, and UI into independent modules.
* **Environment Variable**: System-level key-value pair used to configure applications without changing code.
* **Feature Engineering**: Creating new analytical attributes (`total_amount`, `is_cancellation`) from existing raw columns.

### Interview Keywords to Use
`Modular Architecture` • `Separation of Concerns` • `Data Validation Firewall` • `SQLAlchemy Connection Pool` • `Single Source of Truth` • `Feature Branching` • `Schema Quality Enforcement`
