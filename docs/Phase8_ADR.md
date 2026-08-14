# 🏗️ Phase 8 Architectural Decision Records (ADR)

This document records the key architectural decisions for **Phase 8: Production Cloud Deployment, Containerization & Enterprise Orchestration**.

---

## 📌 ADR 029: Containerization & Non-Root Security Context

* **Decision**: Implement a 2-stage production `Dockerfile` creating non-privileged user `appuser` (UID `10001`).
* **Context**: Production container workloads must adhere to the principle of least privilege, preventing container breakout security risks.
* **Chosen Approach**: Multi-stage build (`builder` -> `runtime`), copying pre-compiled site-packages, executing as non-root user `appuser`.
* **Why**: Minimizes image size (~180MB) and ensures compliance with Kubernetes security standards.

---

## 📌 ADR 030: Cloud-Agnostic Storage Backend & Graceful Fallback

* **Decision**: Extend `StorageBackend` interface with `CloudStorageBackend` (`storage/cloud.py`).
* **Context**: Applications must support local filesystem storage during unit tests and S3-compatible cloud object storage in production.
* **Chosen Approach**: Dependency injection constructor accepting injected S3 client or falling back to in-memory dictionary mock when `boto3` or cloud credentials are absent.
* **Why**: Prevents test suite reliance on live cloud credentials while supporting S3 / GCS cloud object storage.

---

## 📌 ADR 031: Zero-Downtime Cache Layer with Memory Fallback

* **Decision**: Implement `RedisCache` (`analytics/cache.py`) with automatic memory fallback.
* **Context**: Querying complex SQL analytics and monitoring tables repeatedly can strain the analytical database.
* **Chosen Approach**: Redis key-value store with JSON serialization, TTL expiration, hit/miss tracking, and automatic fallback to Python dictionary storage if Redis is offline.
* **Why**: Guarantees zero downtime or data corruption if the caching infrastructure experiences a network partition.
