# 🏗️ Phase 5 Architectural Decision Records (ADR)

This document records the key architectural decisions for **Phase 5: Production Hardening & Deployment**.

---

## 📌 ADR 019: Centralized Validated Production Configuration Engine (`AppConfig`)

* **Decision**: Create a centralized `AppConfig` class in `config/app_config.py` to validate, parse, and enforce application settings across environment profiles (`development`, `testing`, `staging`, `production`).
* **Context**: Application settings were previously read loosely across modules via `os.getenv`, risking runtime crashes or silent credential fallback bugs in production environments.
* **Chosen Approach**: Dataclass-based `AppConfig` with strict profile validation and safe defaults.
* **Why**: Provides strict environment profile checks (`production` mandates DB credentials and custom secret keys), parses numeric types safely, and masks credentials before logging.

---

## 📌 ADR 020: Structured Logging Engine & Sensitive Data Filter

* **Decision**: Implement centralized logging configuration in `config/logging_config.py` with rotating file handlers and regex-based `SensitiveDataFilter`.
* **Context**: Production environments require structured, observable log outputs without emitting database passwords or connection URLs into log files.
* **Chosen Approach**: `StreamHandler` + `RotatingFileHandler` (5MB, 3 backups) with `SensitiveDataFilter`.
* **Why**: Redacts passwords, secret keys, and database connection strings before output while providing consistent timestamps and module names.

---

## 📌 ADR 021: Exponential Backoff Retries for Transient Database Failures

* **Decision**: Implement `execute_with_retry()` in `database/retry.py` with exponential backoff for `TransientDatabaseError` exceptions.
* **Context**: Network glitches or temporary database connection checkout timeouts can cause single-query failures.
* **Chosen Approach**: Exponential backoff retry loop (3 retries, initial delay 0.1s, 2.0x multiplier) differentiating retryable transient errors from non-retryable `PermanentDatabaseError` failures.
* **Why**: Recovers automatically from transient network interruptions without causing pipeline aborts, while failing fast on permanent schema or constraint errors.

---

## 📌 ADR 022: Production Multi-Stage Docker Containerization

* **Decision**: Containerize RetailLens using an optimized `Dockerfile` based on `python:3.10-slim`.
* **Context**: Application deployment requires reproducible runtime environments across cloud platforms (Streamlit Cloud, AWS ECS, GCP Cloud Run).
* **Chosen Approach**: Slim multi-stage `Dockerfile` with HTTP healthcheck (`/_stcore/health`) and comprehensive `.dockerignore`.
* **Why**: Eliminates environment configuration mismatches and provides automated health monitoring.
