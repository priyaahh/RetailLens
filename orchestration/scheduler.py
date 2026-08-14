"""
scheduler.py
------------
Pipeline Execution Scheduler & Concurrency Guard for RetailLens (Phase 7 Milestone 9).
Manages batch execution scheduling (hourly, daily, manual) and enforces concurrency locks
to prevent overlapping pipeline execution runs.
"""

import logging
import threading
from datetime import datetime
from typing import Dict, Optional

from ingestion.pipeline import ETLPipeline, PipelineResult

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """Manages scheduled batch runs and prevents duplicate concurrent executions."""

    def __init__(self, pipeline: Optional[ETLPipeline] = None):
        """Dependency injection constructor."""
        self.pipeline = pipeline or ETLPipeline()
        self._lock = threading.Lock()
        self.is_running = False
        self.last_run_time: Optional[datetime] = None

    def trigger_batch(self, file_path: str, schedule_type: str = "daily") -> PipelineResult:
        """
        Triggers a scheduled pipeline batch execution with concurrency locking.

        :param file_path: Target input dataset file path.
        :param schedule_type: Schedule frequency label ('hourly', 'daily', 'manual').
        :return: PipelineResult object.
        """
        with self._lock:
            if self.is_running:
                logger.warning("Scheduled trigger rejected: A pipeline execution is already in progress.")
                return PipelineResult(
                    status="SKIPPED",
                    error_message="Execution skipped due to active concurrency lock.",
                )
            self.is_running = True

        logger.info("Triggering %s scheduled pipeline execution for file '%s'...", schedule_type, file_path)
        try:
            result = self.pipeline.run(file_path)
            self.last_run_time = datetime.now()
            return result
        finally:
            with self._lock:
                self.is_running = False
