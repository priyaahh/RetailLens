"""
tasks.py
--------
Task Callable Operators for Enterprise Workflow Orchestration (Phase 8 Milestone 9).
Defines isolated task boundary wrappers for Airflow / Prefect task execution.
"""

import logging
from typing import Any, Dict

from ingestion.pipeline import ETLPipeline, PipelineResult

logger = logging.getLogger(__name__)


def task_extract(file_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Extract stage task operator."""
    logger.info("[DAG TASK: EXTRACT] Reading input dataset file '%s'...", file_path)
    context["file_path"] = file_path
    context["stage"] = "EXTRACT"
    return context


def task_validate(context: Dict[str, Any]) -> Dict[str, Any]:
    """Validate stage task operator."""
    logger.info("[DAG TASK: VALIDATE] Executing schema validation...")
    context["stage"] = "VALIDATE"
    return context


def task_clean_transform(context: Dict[str, Any]) -> Dict[str, Any]:
    """Clean & Transform stage task operator."""
    logger.info("[DAG TASK: TRANSFORM] Executing cleaning and feature transformations...")
    context["stage"] = "TRANSFORM"
    return context


def task_load(context: Dict[str, Any]) -> PipelineResult:
    """Database load & audit stage task operator."""
    logger.info("[DAG TASK: LOAD] Executing pipeline orchestrator for file '%s'...", context.get("file_path"))
    pipeline = ETLPipeline()
    result = pipeline.run(context.get("file_path"))
    return result
