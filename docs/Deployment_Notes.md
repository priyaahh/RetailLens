# 🚀 RetailLens Deployment & Containerization Guide

This document provides deployment instructions for running **RetailLens** locally, via Docker containers, or hosted on cloud platforms.

---

## 🐋 1. Local Docker Deployment

### Prerequisites
* Docker Engine 20.10+
* Docker Compose (optional)

### Build Docker Image
```bash
docker build -t retaillens:latest .
```

### Run Docker Container
```bash
docker run -d \
  --name retaillens-app \
  -p 8501:8501 \
  -e APP_ENV=production \
  -e DB_HOST=ep-xyz-123456.us-east-1.aws.neon.tech \
  -e DB_PORT=5432 \
  -e DB_NAME=retaillens_db \
  -e DB_USER=retail_admin \
  -e DB_PASSWORD=your_actual_password_here \
  -e SECRET_KEY=your_actual_secret_key_here \
  retaillens:latest
```

### Verify Container Health
```bash
docker ps
docker logs -f retaillens-app
```
Access dashboard at `http://localhost:8501`.

---

## ☁️ 2. Streamlit Community Cloud Deployment

1. **GitHub Repository Sync**: Push committed code to your GitHub repository.
2. **Streamlit Community Cloud Setup**:
   * Navigate to `share.streamlit.io` and connect your GitHub account.
   * Click **New App**, select your `RetailLens` repository, branch `main`, and main file `app/main.py`.
3. **Configure Cloud Secrets**:
   * In Streamlit Cloud App Settings, navigate to **Secrets**.
   * Add database credentials:
     ```toml
     APP_ENV = "production"
     LOG_LEVEL = "INFO"
     SECRET_KEY = "your_actual_production_secret_key"
     DB_HOST = "ep-xyz-123456.us-east-1.aws.neon.tech"
     DB_PORT = "5432"
     DB_NAME = "retaillens_db"
     DB_USER = "retail_admin"
     DB_PASSWORD = "your_actual_password"
     DB_SSLMODE = "require"
     ```
4. **Deploy**: Streamlit Community Cloud automatically installs `requirements.txt` and launches the application.
