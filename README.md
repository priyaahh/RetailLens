# 🚀 RetailLens – End-to-End Retail Analytics, Distributed Data & Production Cloud Platform

[![RetailLens CI Pipeline](https://github.com/retail-analytics/RetailLens/actions/workflows/ci.yml/badge.svg)](https://github.com/retail-analytics/RetailLens/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://python.org)
[![PySpark](https://img.shields.io/badge/pyspark-3.5%2B-orange.svg)](https://spark.apache.org)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-blue.svg)](https://kubernetes.io)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15%2B-blue.svg)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red.svg)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/docker-ready-cyan.svg)](https://docker.com)

RetailLens is an enterprise-grade retail analytics platform built with Python, PySpark, PostgreSQL, Streamlit, Docker, Kubernetes, Prometheus, Redis, and GitHub Actions. It ingests raw transaction datasets, executes automated schema and data quality validation, runs a modular hybrid compute ETL pipeline (routing jobs between single-node Pandas and distributed PySpark based on dataset file size), manages a Parquet Data Lake with temporal partitioning (`year=YYYY/month=MM`), records pipeline run audits and data lineage provenance, stores structured fact tables in a cloud PostgreSQL database with connection pooling, and exposes a production REST API boundary, Prometheus operational metrics exporter, zero-downtime Redis caching, and an interactive Streamlit BI web application.

---

## ✨ System Highlights (Phases 1–8 Completed)

* 🐋 **Multi-Stage Containerization**: 2-stage production `Dockerfile` running as non-root user (`appuser` UID `10001`) with HTTP healthchecks, `docker-compose.yml`, and clean `.dockerignore`.
* ⚡ **Hybrid Compute Routing Engine**: `ComputeRouter` dynamically evaluates dataset file size, routing small files (< 100MB) to Pandas for zero-overhead execution and large files (>= 100MB) to PySpark for distributed Catalyst-optimized cluster execution.
* 🌲 **Parquet Data Lake Storage Layer**: `ParquetDataLake` managing raw, staged, and processed data lake zones using Snappy-compressed Parquet storage partitioned by year and month (`year=YYYY/month=MM`).
* ☁️ **Cloud-Agnostic Storage Abstraction**: Abstract `StorageBackend` interface with `CloudStorageBackend` (`storage/cloud.py`) supporting S3-compatible cloud object storage with in-memory mock fallback.
* 🐘 **Database Connection Pooling**: `create_pooled_engine()` and `check_db_health()` (`database/pool.py`) providing pre-ping connection validation and configurable pool parameters (`db_pool_size=10`).
* ⚡ **Redis & Memory Fallback Cache**: `RedisCache` (`analytics/cache.py`) supporting key TTL expiration, hit/miss metric tracking, and zero-downtime memory fallback.
* 🔌 **Production REST API Boundary**: `RetailLensAPI` (`api/app.py`) providing REST endpoints (`GET /health`, `GET /ready`, `GET /metrics`, `GET /pipeline/runs`, `GET /pipeline/quality`, `GET /analytics/kpis`).
* 📊 **Prometheus Operational Metrics**: `PrometheusMetricsExporter` (`analytics/metrics.py`) exporting metrics in standard Prometheus exposition text format.
* ☸️ **Production Kubernetes Architecture**: Kubernetes manifests (`deploy/kubernetes/`) containing Namespace, ConfigMap, Secret, Deployment, Service, Ingress TLS, and HPA autoscaling.
* 🤖 **Multi-Stage CI/CD Pipeline**: GitHub Actions CI workflow (`ci.yml`) automating linting, unit test validation across 31 test modules, and Docker container build validation.

---

## 📚 Documentation & Engineering Notes

Detailed technical notes, architectural decision records (ADR), and technical interview preparation materials are organized in the [`docs/`](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs) directory:

* 📄 [**Phase 1 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase1_Notes.md) – Project foundation & initial architecture.
* 📄 [**Phase 2 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase2_Notes.md) – Data Ingestion, Data Quality Validation, Cleaning, and Staging.
* 📄 [**Phase 3 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase3_Notes.md) – PostgreSQL Relational Schema, Master SQL Catalog, Window Functions, and Indexing.
* 📄 [**Phase 4 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase4_Notes.md) – Streamlit Web App Architecture, UI Components, and Caching.
* 📄 [**Phase 5 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase5_Notes.md) – Production Hardening, Configuration, Observability, Reliability, Security, CI/CD, and Docker.
* 📄 [**Phase 6 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase6_Notes.md) – Incremental ETL, Watermark Management, Pipeline Run Tracking, Data Lineage, and Operational Views.
* 📄 [**Phase 7 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase7_Notes.md) – Scale-Out Data Engineering, PySpark Engine, Parquet Lake, Storage Abstraction, and DAG Orchestration.
* 📄 [**Phase 8 Notes**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase8_Notes.md) – Production Cloud Deployment, Containerization, Kubernetes, REST API, Redis, and Prometheus Metrics.
* 📄 [**Phase 8 Deployment**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase8_Deployment.md) – Complete Docker Compose & Kubernetes operations guide.
* 📄 [**Phase 8 Security Audit**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Phase8_Security_Audit.md) – Master security vulnerability audit and hardening report.
* 📄 [**Interview Q&A Guide**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Interview_QA.md) – Master Q&A bank with 75 interview questions across software engineering, data engineering, SQL, system design, security, CI/CD, Docker, Kubernetes, PySpark, Parquet, and cloud architecture.
* 📄 [**Production Checklist**](file:///c:/Users/priya/OneDrive/Desktop/RetailLens/docs/Production_Checklist.md) – Master 40-point production readiness evaluation.

---

## 📐 Enterprise System Architecture

```text
USERS / HTTP Clients
         │
         ▼
Kubernetes Ingress (TLS SSL Termination)
         │
         ├──► Streamlit BI Web Dashboard (Port 8501)
         │
         └──► Production REST API Boundary (Port 8000: /health, /ready, /metrics, /pipeline/runs)
                     │
                     ▼
Orchestrated Pipeline Service & Enterprise DAG Scheduler
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
Single-Node Pandas          Distributed PySpark
       │                           │
       └─────────────┬─────────────┘
                     │
                     ▼
S3 / GCS Cloud Object Storage Lake (storage/cloud.py)
                     │
                     ▼
Managed Cloud PostgreSQL / Neon Database (database/pool.py)
                     │
       ┌─────────────┴─────────────┐
       ▼                           ▼
Redis Caching Layer        Prometheus Metrics Exporter
(analytics/cache.py)       (analytics/metrics.py)
```

---

## ⚡ Quick Start Setup

### 1. Local Setup
```bash
git clone <repo-url>
cd RetailLens

python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1 | Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

# Run Dashboard
streamlit run app/main.py

# Run Full Test Suite (31 Test Modules, 77 Tests)
python -m unittest discover tests -v
```

### 2. Docker Container & Kubernetes Setup
```bash
# Docker Compose Local Setup
docker-compose up --build -d

# Kubernetes Production Deployment
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.example.yaml
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
kubectl apply -f deploy/kubernetes/hpa.yaml
```
