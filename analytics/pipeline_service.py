"""
pipeline_service.py
-------------------
Pipeline Monitoring Service Layer for RetailLens (Phase 6 Milestone 9).
Provides high-level operational monitoring status APIs, run summaries, lineage tracking,
and data quality summaries for the Streamlit BI UI.
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd

from analytics.pipeline_repository import PipelineMonitoringRepository

logger = logging.getLogger(__name__)


class PipelineMonitoringService:
    """Service facade decoupling the Streamlit UI from pipeline audit database operations."""

    def __init__(self, repository: Optional[PipelineMonitoringRepository] = None):
        """Dependency injection constructor."""
        self.repository = repository or PipelineMonitoringRepository()

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Returns metadata dictionary of the latest pipeline execution run."""
        return self.repository.get_latest_run()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Returns metadata dictionary for a specific run_id."""
        return self.repository.get_run(run_id)

    def get_recent_runs(self, limit: int = 20) -> pd.DataFrame:
        """Returns DataFrame of recent pipeline runs."""
        return self.repository.get_recent_runs(limit=limit)

    def get_failed_runs(self, limit: int = 20) -> pd.DataFrame:
        """Returns DataFrame of failed pipeline runs."""
        return self.repository.get_failed_runs(limit=limit)

    def get_daily_summary(self, limit_days: int = 30) -> pd.DataFrame:
        """Returns aggregated daily pipeline run metrics."""
        return self.repository.get_daily_summary(limit_days=limit_days)

    def get_data_quality_summary(self, limit: int = 20) -> pd.DataFrame:
        """Returns data quality metrics DataFrame."""
        return self.repository.get_data_quality_summary(limit=limit)

    def get_lineage(self, run_id: Optional[str] = None, limit: int = 20) -> pd.DataFrame:
        """Returns data lineage provenance DataFrame."""
        return self.repository.get_lineage(run_id=run_id, limit=limit)

    def get_pipeline_health_status(self) -> Dict[str, Any]:
        """Calculates overall pipeline system health metrics and badge status."""
        recent_df = self.get_recent_runs(limit=50)

        if recent_df.empty:
            return {
                "health_status": "NO_RUNS",
                "success_rate_pct": 100.0,
                "total_runs": 0,
                "failed_runs": 0,
                "total_rows_inserted": 0,
                "avg_duration_seconds": 0.0,
            }

        total_runs = len(recent_df)
        failed_runs = len(recent_df[recent_df["status"] == "FAILED"])
        successful_runs = len(recent_df[recent_df["status"] == "SUCCESS"])
        success_rate = round((successful_runs / total_runs) * 100, 1)
        total_inserted = int(recent_df["rows_inserted"].sum()) if "rows_inserted" in recent_df.columns else 0
        avg_duration = round(float(recent_df["execution_duration"].mean()), 2) if "execution_duration" in recent_df.columns else 0.0

        health_status = "HEALTHY"
        if success_rate < 80.0 or failed_runs > 2:
            health_status = "CRITICAL"
        elif success_rate < 95.0 or failed_runs > 0:
            health_status = "WARNING"

        return {
            "health_status": health_status,
            "success_rate_pct": success_rate,
            "total_runs": total_runs,
            "failed_runs": failed_runs,
            "total_rows_inserted": total_inserted,
            "avg_duration_seconds": avg_duration,
        }
