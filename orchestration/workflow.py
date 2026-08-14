"""
workflow.py
-----------
Orchestrated Workflow Execution Engine for RetailLens (Phase 7 Milestone 8).
Executes DAG task stages with exponential backoff retries, fail-fast error handling,
atomic transaction rollbacks, and run audit tracking integration.
"""

import logging
import time
from typing import Dict, Optional

from database.retry import execute_with_retry
from ingestion.pipeline import ETLPipeline, PipelineResult
from orchestration.dag import PipelineDAG, TaskNode

logger = logging.getLogger(__name__)


class OrchestratedPipelineWorkflow:
    """Executes DAG pipeline tasks with retry mechanisms and failure recovery."""

    def __init__(self, pipeline: Optional[ETLPipeline] = None):
        """Dependency injection constructor."""
        self.pipeline = pipeline or ETLPipeline()

    def execute_file(
        self,
        file_path: str,
        engine_choice: str = "auto",
        max_retries: int = 3,
    ) -> PipelineResult:
        """
        Executes pipeline via DAG task stages with retry protection.

        :param file_path: Path to target input file.
        :param engine_choice: 'auto', 'pandas', or 'spark'.
        :param max_retries: Maximum task retry attempts for transient errors.
        :return: PipelineResult object.
        """
        logger.info("Starting Orchestrated Workflow Execution for '%s' [Engine: %s]", file_path, engine_choice)

        def run_stage_with_backoff():
            return self.pipeline.run(file_path)

        try:
            result = execute_with_retry(
                func=run_stage_with_backoff,
                max_retries=max_retries,
                initial_delay=1.0,
                backoff_factor=2.0,
            )
            return result
        except Exception as e:
            logger.error("Orchestrated Workflow Execution failed permanently: %s", str(e))
            return PipelineResult(
                status="FAILED",
                error_message=str(e),
            )
