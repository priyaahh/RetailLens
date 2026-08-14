# ⚡ Phase 8 Cheat Sheet (5-Minute Production Deployment Revision Guide)

---

## 📐 Enterprise Architecture Flow

```text
Ingress / API ──► Streamlit UI / REST API ──► Orchestrated Pipeline ──► PySpark / Pandas ──► Cloud S3 Storage ──► Neon PostgreSQL ──► Redis / Prometheus
```

---

## 🔑 Key Deployment & Observability Terms

* **Multi-Stage Docker Build**: Dockerfile pattern separating build-time compilation dependencies from final lightweight runtime images.
* **Liveness vs Readiness Probes**: Liveness (`/health`) checks if container process is alive; Readiness (`/ready`) verifies downstream database/storage connectivity before routing traffic.
* **Prometheus Metrics Protocol**: Standardized text exposition format exporting counters and gauges (`pipeline_runs_total`, `rows_inserted_total`).
* **Connection Pooling**: Reusing database connections (`db_pool_size=10`) to eliminate connection handshake latency and prevent database socket exhaustion.
* **Horizontal Pod Autoscaler (HPA)**: Kubernetes controller dynamically scaling pod replicas based on CPU/memory utilization thresholds (75% CPU target).

---

## 💡 Top Phase 8 Interview Talking Points

1. *"We containerized RetailLens using a multi-stage Dockerfile running under a non-root security context (`appuser` UID `10001`) with HTTP healthchecks."*
2. *"Our REST API layer (`api/app.py`) cleanly separates Liveness (`/health`) and Readiness (`/ready`) probes, verifying database connection pool health before admitting user traffic."*
3. *"We integrated Prometheus metrics (`analytics/metrics.py`) and Redis caching (`analytics/cache.py`) with zero-downtime memory fallback, ensuring application stability if Redis is offline."*
4. *"We created production Kubernetes manifests (`deploy/kubernetes/`) with ConfigMaps, Secrets, Ingress TLS, and HPA autoscaling from 2 to 10 pods."*
