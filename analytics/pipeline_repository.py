"""
pipeline_repository.py
----------------------
Data Access Layer for Operational Pipeline Audit & Monitoring (Phase 6 Milestone 9).
Provides SQL query execution against pipeline_runs, data_lineage, and operational monitoring views,
decoupling database access from the monitoring service and UI components.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class PipelineMonitoringRepository:
    """Repository executing parameterized queries against pipeline audit tables and operational views."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        self.engine = engine or get_db_engine()

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Retrieves the most recent pipeline_runs execution record."""
        query = "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT 1;"
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(query)).mappings().first()
                return dict(res) if res else None
        except Exception as e:
            logger.warning("Could not fetch latest pipeline run: %s", str(e))
            return None

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves execution record for a specific run_id."""
        query = "SELECT * FROM pipeline_runs WHERE run_id = :run_id;"
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(query), {"run_id": run_id}).mappings().first()
                return dict(res) if res else None
        except Exception as e:
            logger.warning("Could not fetch run '%s': %s", run_id, str(e))
            return None

    def get_recent_runs(self, limit: int = 20) -> pd.DataFrame:
        """Retrieves DataFrame of recent pipeline runs."""
        query = "SELECT * FROM pipeline_runs ORDER BY started_at DESC LIMIT :limit;"
        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(sql=text(query), con=conn, params={"limit": limit})
        except Exception as e:
            logger.warning("Could not fetch recent runs: %s", str(e))
            return pd.DataFrame()

    def get_failed_runs(self, limit: int = 20) -> pd.DataFrame:
        """Retrieves DataFrame of failed pipeline runs."""
        query = "SELECT * FROM pipeline_runs WHERE status = 'FAILED' ORDER BY started_at DESC LIMIT :limit;"
        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(sql=text(query), con=conn, params={"limit": limit})
        except Exception as e:
            logger.warning("Could not fetch failed runs: %s", str(e))
            return pd.DataFrame()

    def get_daily_summary(self, limit_days: int = 30) -> pd.DataFrame:
        """Retrieves aggregated daily pipeline run statistics."""
        query = """
            SELECT 
                DATE(started_at) AS run_date,
                COUNT(*) AS total_runs,
                COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) AS successful_runs,
                COUNT(CASE WHEN status = 'FAILED' THEN 1 END) AS failed_runs,
                SUM(rows_read) AS total_rows_read,
                SUM(rows_inserted) AS total_rows_inserted,
                SUM(rows_skipped) AS total_rows_skipped,
                ROUND(AVG(execution_duration), 2) AS avg_duration_seconds
            FROM pipeline_runs
            GROUP BY DATE(started_at)
            ORDER BY run_date DESC
            LIMIT :limit_days;
        """
        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(sql=text(query), con=conn, params={"limit_days": limit_days})
        except Exception as e:
            logger.warning("Could not fetch daily summary: %s", str(e))
            return pd.DataFrame()

    def get_data_quality_summary(self, limit: int = 20) -> pd.DataFrame:
        """Retrieves data quality metrics for recent pipeline runs."""
        query = """
            SELECT 
                run_id,
                source_file,
                rows_read,
                rows_valid,
                rows_invalid,
                CASE 
                    WHEN rows_read > 0 THEN ROUND((1.0 * rows_valid / rows_read) * 100, 2)
                    ELSE 100.00 
                END AS data_quality_rate_pct,
                started_at
            FROM pipeline_runs
            ORDER BY started_at DESC
            LIMIT :limit;
        """
        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(sql=text(query), con=conn, params={"limit": limit})
        except Exception as e:
            logger.warning("Could not fetch data quality summary: %s", str(e))
            return pd.DataFrame()

    def get_lineage(self, run_id: Optional[str] = None, limit: int = 20) -> pd.DataFrame:
        """Retrieves data lineage records."""
        if run_id:
            query = "SELECT * FROM data_lineage WHERE run_id = :run_id ORDER BY created_at DESC;"
            params = {"run_id": run_id}
        else:
            query = "SELECT * FROM data_lineage ORDER BY created_at DESC LIMIT :limit;"
            params = {"limit": limit}

        try:
            with self.engine.connect() as conn:
                return pd.read_sql_query(sql=text(query), con=conn, params=params)
        except Exception as e:
            logger.warning("Could not fetch data lineage: %s", str(e))
            return pd.DataFrame()
