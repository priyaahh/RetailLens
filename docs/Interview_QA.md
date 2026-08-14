# 🎯 Master Technical Interview Q&A Bank (Phases 1–8)

This document contains a production-grade interview question bank derived from **Phases 1, 2, 3, 4, 5, 6, 7 & 8**. Use this guide to prepare for technical interview rounds across Data Engineering, Software Engineering, Backend Development, SQL, System Design, DevOps, Kubernetes, Cloud Architecture, and Production Deployment.

---

## 🛠️ 1. Software Engineering & Architecture

### Q1: What is modular architecture, and how is it implemented in RetailLens?
**Model Answer**:
Modular architecture is a design pattern where an application is decomposed into independent, self-contained modules—each responsible for a single business capability. In RetailLens, we separate concerns across distinct directories: `ingestion/` handles data reading and file parsing, `database/` manages database connections and queries, `analytics/` processes metric calculations and ML models, and `app/` controls the UI. This ensures high cohesion within modules and loose coupling between modules, making the system testable and easy to maintain.

---

## ⚡ 7. Scale-Out Data Engineering & PySpark (Phase 7)

### Q58: What are the primary scalability bottlenecks of single-node Pandas ETL pipelines?
* **Strong Answer**: Single-node Pandas pipelines suffer from two major bottlenecks: **RAM memory saturation** and **single-threaded CPU execution**. Pandas requires contiguous memory in RAM (needing 5x–10x dataset size in free memory), leading to OOM crashes for datasets > 10GB. Furthermore, Pandas executes transformations on a single CPU core, failing to utilize multi-core clusters or cloud worker nodes.
* **Keywords**: `RAM Saturation`, `OOM Crash`, `Single-Threaded CPU`, `Contiguous Memory`.

---

## 🐋 8. Production Cloud Deployment, Kubernetes & Observability (Phase 8)

### Q66: What is the benefit of Multi-Stage Docker Builds in production?
* **Strong Answer**: Multi-Stage Docker Builds separate heavy build-time dependencies (compilers, build tools) from runtime artifacts. In RetailLens, Stage 1 (`builder`) compiles Python packages into a temporary directory, while Stage 2 (`runtime`) copies only the pre-compiled packages into a lightweight `python:3.10-slim` image, reducing image size by 70% and removing build-tool security vulnerabilities.
* **Keywords**: `Multi-Stage Build`, `Image Size Reduction`, `Security Hardening`, `Least Privilege`.

### Q67: What is the difference between Liveness and Readiness Probes in Kubernetes?
* **Strong Answer**: A **Liveness Probe** (`/health`) checks if the container process is running. If it fails, Kubernetes restarts the pod container. A **Readiness Probe** (`/ready`) checks if the application is ready to serve traffic by verifying database connection pool health and storage readiness. If it fails, Kubernetes removes the pod IP from service load balancer endpoints without restarting it.
* **Keywords**: `Liveness Probe`, `Readiness Probe`, `Pod Lifecycle`, `Health Checks`.

### Q68: How do you design a zero-downtime Redis caching layer with fallback?
* **Strong Answer**: In `RedisCache` (`analytics/cache.py`), we wrap all Redis GET/SET calls in exception handlers. If Redis is unavailable or fails to connect, the client logs a warning and seamlessly falls back to an in-memory Python dictionary cache (`_memory_cache`). This guarantees zero application downtime or data loss if Redis experiences a network partition.
* **Keywords**: `Redis Cache`, `Zero-Downtime Fallback`, `In-Memory Store`, `TTL Expiration`.

### Q69: How do you export Prometheus operational metrics in Python?
* **Strong Answer**: `PrometheusMetricsExporter` (`analytics/metrics.py`) tracks counters (`pipeline_runs_total`, `rows_inserted_total`), gauges (`data_quality_score`), and hit/miss stats. It exposes these metrics via the `export_prometheus_text()` method in standard Prometheus Exposition Text Format for scraping by Prometheus server daemons.
* **Keywords**: `Prometheus Metrics`, `Counters & Gauges`, `Exposition Protocol`, `Observability`.

### Q70: How do Kubernetes ConfigMaps and Secrets differ?
* **Strong Answer**: **ConfigMaps** store non-sensitive configuration parameters (such as `APP_ENV`, `LOG_LEVEL`, `DB_PORT`) in plain text. **Secrets** store sensitive credentials (database passwords, API secret keys) encoded in Base64 (or encrypted at rest). Both are injected into pod containers as environment variables or mounted volume files.
* **Keywords**: `ConfigMap`, `Secret`, `Environment Injection`, `Base64 Encoding`.

### Q71: How does Horizontal Pod Autoscaler (HPA) auto-scale workloads in Kubernetes?
* **Strong Answer**: HPA periodically queries the Kubernetes Metrics Server to measure resource utilization. If CPU utilization exceeds 75% or memory utilization exceeds 80%, HPA automatically increases the replica count of the `retaillens-app` deployment from 2 up to 10 pods, scaling back down when load decreases.
* **Keywords**: `HPA`, `Autoscaling`, `Target Utilization`, `Replica Scaling`.

### Q72: What is the purpose of database connection pooling in high-concurrency production applications?
* **Strong Answer**: Opening a new database TCP connection for every query incurs substantial network latency and socket allocation overhead. A connection pool (`create_pooled_engine` in `database/pool.py`) maintains a reusable pool of open connections (`db_pool_size=10`), reusing connections across requests, pre-pinging health (`pool_pre_ping=True`), and preventing database connection exhaustion.
* **Keywords**: `Connection Pooling`, `SQLAlchemy Pool`, `Pre-Ping Health`, `Socket Reuse`.

### Q73: How do you secure containerized applications in Kubernetes?
* **Strong Answer**: We enforce container security by:
  1. Running processes under a non-root user (`appuser` UID `10001`).
  2. Setting resource requests and limits (`cpu: 250m`, `memory: 512Mi`).
  3. Disabling container privilege escalation (`runAsNonRoot: true`).
  4. Masking passwords in logs via `SensitiveDataFilter`.
  5. Excluding `.env` files from Docker contexts using `.dockerignore`.
* **Keywords**: `Non-Root Security Context`, `Resource Limits`, `Least Privilege`, `Secret Masking`.

### Q74: What is a Rolling Update deployment strategy in Kubernetes?
* **Strong Answer**: A Rolling Update updates pod instances incrementally with zero downtime. By setting `maxSurge: 1` and `maxUnavailable: 0`, Kubernetes starts 1 new pod container running the updated image and waits for its readiness probe to pass before terminating an old pod, ensuring service availability throughout the deployment.
* **Keywords**: `Rolling Update`, `Zero-Downtime Deployment`, `maxSurge`, `maxUnavailable`.

### Q75: How does CI/CD enforce production quality before deployment?
* **Strong Answer**: Our GitHub Actions CI pipeline (`.github/workflows/ci.yml`) runs on every push and pull request. It executes a multi-stage validation workflow: (1) unit and integration tests across 31 test modules, (2) environment configuration validation, (3) security checks, and (4) multi-stage Docker image build validation. If any unit test fails, the CI workflow blocks deployment to production.
* **Keywords**: `CI/CD Pipeline`, `GitHub Actions`, `Automated Testing`, `Build Validation`.
