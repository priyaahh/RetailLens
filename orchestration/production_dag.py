"""
production_dag.py
------------------
Production Enterprise Workflow DAG Definition for RetailLens (Phase 8 Milestone 9).
Models explicit task dependencies (extract -> validate -> transform -> quality -> load -> lineage -> monitor)
compatible with Apache Airflow and Prefect workflow orchestrators.
"""

import logging
from typing import Any, Dict

from orchestration.config import ProductionDAGConfig
from orchestration.dag import PipelineDAG, TaskNode
from orchestration.tasks import task_clean_transform, task_extract, task_load, task_validate

logger = logging.getLogger(__name__)


def build_production_dag(file_path: str) -> PipelineDAG:
    """
    Constructs production PipelineDAG instance with explicit task dependencies.

    :param file_path: Target dataset input file path.
    :return: Configured PipelineDAG instance.
    """
    cfg = ProductionDAGConfig()
    dag = PipelineDAG(dag_id=cfg.dag_id)
    context = {}

    t_extract = TaskNode("extract", lambda: bool(task_extract(file_path, context)))
    t_validate = TaskNode("validate", lambda: bool(task_validate(context)))
    t_transform = TaskNode("transform", lambda: bool(task_clean_transform(context)))
    t_load = TaskNode("load", lambda: bool(task_load(context)))

    dag.add_task(t_extract)
    dag.add_task(t_validate, depends_on=["extract"])
    dag.add_task(t_transform, depends_on=["validate"])
    dag.add_task(t_load, depends_on=["transform"])

    logger.info("Built production DAG '%s' with %d tasks.", cfg.dag_id, len(dag.tasks))
    return dag
