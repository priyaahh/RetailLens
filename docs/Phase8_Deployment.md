# 🚀 Phase 8 Cloud Deployment & Kubernetes Operations Guide

This guide details instructions for deploying **RetailLens** in containerized Docker and production Kubernetes environments.

---

## 🐋 1. Local Docker & Docker Compose Execution

```bash
# 1. Build Multi-Stage Docker Image
docker build -t retaillens:latest .

# 2. Run Container Standalone
docker run -d -p 8501:8501 -p 8000:8000 --env-file .env retaillens:latest

# 3. Multi-Container Execution with Docker Compose
docker-compose up --build -d
```

---

## ☸️ 2. Production Kubernetes Deployment

```bash
# 1. Create Namespace
kubectl apply -f deploy/kubernetes/namespace.yaml

# 2. Apply ConfigMap and Secret
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/secret.example.yaml

# 3. Deploy Application and Services
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
kubectl apply -f deploy/kubernetes/hpa.yaml

# 4. Monitor Deployment & Pod Health
kubectl get pods -n retaillens-prod -w
kubectl get hpa -n retaillens-prod
```
