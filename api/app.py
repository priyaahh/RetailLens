"""
app.py
------
Production API Service Layer Endpoint Dispatcher for RetailLens (Phase 8 Milestone 6).
Provides REST endpoints (/health, /ready, /metrics, /pipeline/runs, /pipeline/quality, /analytics/kpis)
with request validation, structured JSON responses, proper status codes, and security masking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from analytics.kpis import KPICalculator
from analytics.pipeline_service import PipelineMonitoringService
from analytics.service import AnalyticsService
from database.connection import get_db_engine
from database.pool import check_db_health

logger = logging.getLogger(__name__)


class RetailLensAPI:
    """Production REST API Dispatcher."""

    def __init__(
        self,
        analytics_service: Optional[AnalyticsService] = None,
        monitoring_service: Optional[PipelineMonitoringService] = None,
    ):
        """Dependency injection constructor."""
        self.analytics_service = analytics_service or AnalyticsService()
        self.monitoring_service = monitoring_service or PipelineMonitoringService()
        self.engine = get_db_engine()

    def handle_request(self, path: str, params: Optional[Dict[str, Any]] = None) -> Tuple[int, Dict[str, Any]]:
        """
        Dispatches HTTP path request and returns (status_code, response_payload).

        :param path: Request endpoint path string (e.g. '/health', '/analytics/kpis').
        :param params: Optional query parameters dictionary.
        :return: Tuple of (http_status_code, json_dict_response).
        """
        clean_path = path.strip().rstrip("/")
        params = params or {}

        try:
            # 1. GET /health (Liveness Probe)
            if clean_path == "/health":
                return 200, {
                    "status": "HEALTHY",
                    "timestamp": datetime.now().isoformat(),
                    "service": "RetailLens API",
                }

            # 2. GET /ready (Readiness Probe)
            if clean_path == "/ready":
                db_health = check_db_health(self.engine)
                is_ready = db_health.get("status") == "HEALTHY"
                status_code = 200 if is_ready else 503
                return status_code, {
                    "status": "READY" if is_ready else "NOT_READY",
                    "database": db_health,
                    "timestamp": datetime.now().isoformat(),
                }

            # 3. GET /pipeline/runs
            if clean_path == "/pipeline/runs":
                limit = int(params.get("limit", 20))
                runs_df = self.monitoring_service.get_recent_runs(limit=limit)
                return 200, {
                    "status": "SUCCESS",
                    "count": len(runs_df),
                    "data": runs_df.to_dict(orient="records") if not runs_df.empty else [],
                }

            # 4. GET /pipeline/runs/{run_id}
            if clean_path.startswith("/pipeline/runs/"):
                run_id = clean_path.split("/")[-1]
                run_data = self.monitoring_service.get_run(run_id)
                if run_data:
                    return 200, {"status": "SUCCESS", "data": run_data}
                return 404, {"status": "ERROR", "message": f"Run ID '{run_id}' not found."}

            # 5. GET /pipeline/quality
            if clean_path == "/pipeline/quality":
                limit = int(params.get("limit", 20))
                dq_df = self.monitoring_service.get_data_quality_summary(limit=limit)
                return 200, {
                    "status": "SUCCESS",
                    "count": len(dq_df),
                    "data": dq_df.to_dict(orient="records") if not dq_df.empty else [],
                }

            # 6. GET /analytics/kpis
            if clean_path == "/analytics/kpis":
                kpis = self.analytics_service.kpi_engine.get_all_kpis()
                return 200, {
                    "status": "SUCCESS",
                    "data": kpis,
                    "timestamp": datetime.now().isoformat(),
                }

            # Endpoint Not Found
            return 404, {"status": "ERROR", "message": f"Endpoint '{clean_path}' not found."}

        except Exception as e:
            logger.error("API endpoint execution error for '%s': %s", clean_path, str(e), exc_info=True)
            return 500, {
                "status": "ERROR",
                "message": "Internal Server Error",
                "error_details": str(e),
            }
