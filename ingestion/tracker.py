"""
tracker.py
----------
Pipeline Run Tracking Engine for RetailLens (Phase 6 Milestone 2).
Provides atomic pipeline execution audit tracking across database operations,
handling run status transitions (RUNNING, SUCCESS, FAILED, PARTIAL, SKIPPED), row counts, timing, and error logs.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class PipelineRunTracker:
    """Manages audit execution records in the pipeline_runs database table."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        self.engine = engine or get_db_engine()

    def start_run(
        self,
        source_file: str,
        source_hash: str,
        pipeline_name: str = "RetailLens_ETL",
        watermark_before: Optional[datetime] = None,
    ) -> str:
        """
        Registers a new pipeline execution run in RUNNING status.

        :param source_file: Target raw dataset file path.
        :param source_hash: SHA-256 hash of the input file.
        :param pipeline_name: Name of the pipeline process.
        :param watermark_before: Initial high-watermark timestamp before execution.
        :return: Generated unique run_id UUID string.
        """
        run_id = str(uuid.uuid4())
        started_at = datetime.now()

        query = """
            INSERT INTO pipeline_runs (
                run_id, pipeline_name, started_at, status, source_file, source_hash, watermark_before
            ) VALUES (
                :run_id, :pipeline_name, :started_at, 'RUNNING', :source_file, :source_hash, :watermark_before
            );
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {
                        "run_id": run_id,
                        "pipeline_name": pipeline_name,
                        "started_at": started_at,
                        "source_file": str(source_file),
                        "source_hash": source_hash,
                        "watermark_before": watermark_before,
                    },
                )
            logger.info("Pipeline run started: ID '%s' | File: '%s'", run_id, source_file)
        except Exception as e:
            logger.warning("Unable to insert pipeline run record in database: %s", str(e))

        return run_id

    def complete_run(
        self,
        run_id: str,
        rows_read: int,
        rows_valid: int,
        rows_invalid: int,
        rows_transformed: int,
        rows_inserted: int,
        rows_skipped: int,
        watermark_after: Optional[datetime] = None,
        execution_duration: float = 0.0,
        status: str = "SUCCESS",
    ) -> bool:
        """
        Marks a pipeline run as successfully completed or partially completed.

        :param run_id: Execution run ID string.
        :param rows_read: Total raw rows read.
        :param rows_valid: Validated rows count.
        :param rows_invalid: Invalid/rejected rows count.
        :param rows_transformed: Feature-engineered rows count.
        :param rows_inserted: Database rows persisted count.
        :param rows_skipped: Incremental duplicate skipped count.
        :param watermark_after: Updated high-watermark timestamp.
        :param execution_duration: Total execution duration in seconds.
        :param status: SUCCESS, PARTIAL, or SKIPPED.
        :return: True on success.
        """
        completed_at = datetime.now()
        query = """
            UPDATE pipeline_runs
            SET completed_at = :completed_at,
                status = :status,
                rows_read = :rows_read,
                rows_valid = :rows_valid,
                rows_invalid = :rows_invalid,
                rows_transformed = :rows_transformed,
                rows_inserted = :rows_inserted,
                rows_skipped = :rows_skipped,
                execution_duration = :execution_duration,
                watermark_after = :watermark_after
            WHERE run_id = :run_id;
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {
                        "run_id": run_id,
                        "completed_at": completed_at,
                        "status": status,
                        "rows_read": rows_read,
                        "rows_valid": rows_valid,
                        "rows_invalid": rows_invalid,
                        "rows_transformed": rows_transformed,
                        "rows_inserted": rows_inserted,
                        "rows_skipped": rows_skipped,
                        "execution_duration": round(execution_duration, 3),
                        "watermark_after": watermark_after,
                    },
                )
            logger.info("Pipeline run completed: ID '%s' | Status: %s | Duration: %.3fs", run_id, status, execution_duration)
            return True
        except Exception as e:
            logger.warning("Failed to update completed run in database: %s", str(e))
            return False

    def fail_run(self, run_id: str, error_message: str, execution_duration: float = 0.0) -> bool:
        """
        Marks a pipeline run as FAILED and logs error details.

        :param run_id: Execution run ID string.
        :param error_message: Exception failure message string.
        :param execution_duration: Execution duration until failure in seconds.
        :return: True on success.
        """
        completed_at = datetime.now()
        query = """
            UPDATE pipeline_runs
            SET completed_at = :completed_at,
                status = 'FAILED',
                error_message = :error_message,
                execution_duration = :execution_duration
            WHERE run_id = :run_id;
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {
                        "run_id": run_id,
                        "completed_at": completed_at,
                        "error_message": str(error_message),
                        "execution_duration": round(execution_duration, 3),
                    },
                )
            logger.error("Pipeline run marked FAILED: ID '%s' | Error: %s", run_id, error_message)
            return True
        except Exception as e:
            logger.warning("Failed to mark failed run in database: %s", str(e))
            return False

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches execution metadata for a given run_id.

        :param run_id: Execution run UUID string.
        :return: Dictionary of column values or None.
        """
        query = "SELECT * FROM pipeline_runs WHERE run_id = :run_id;"
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(query), {"run_id": run_id}).mappings().first()
                return dict(res) if res else None
        except Exception as e:
            logger.warning("Could not fetch run metadata for '%s': %s", run_id, str(e))
            return None
