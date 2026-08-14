"""
dag.py
------
Directed Acyclic Graph (DAG) Pipeline Orchestration Model for RetailLens (Phase 7 Milestone 7).
Models explicit task stage dependencies (extract -> validate -> clean -> transform -> quality_check -> load -> lineage -> monitoring).
"""

import logging
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class TaskNode:
    """Represents an individual stage task in an orchestrated DAG pipeline."""

    def __init__(
        self,
        task_id: str,
        action: Callable[[], bool],
        retries: int = 3,
        retry_delay_seconds: float = 1.0,
    ):
        self.task_id = task_id
        self.action = action
        self.retries = retries
        self.retry_delay_seconds = retry_delay_seconds
        self.upstream_tasks: Set[str] = set()
        self.status = "PENDING"  # PENDING, RUNNING, SUCCESS, FAILED, SKIPPED

    def add_upstream(self, task_id: str) -> None:
        """Sets upstream dependency task_id."""
        self.upstream_tasks.add(task_id)


class PipelineDAG:
    """Manages DAG task ordering and dependency resolution."""

    def __init__(self, dag_id: str = "RetailLens_Orchestrated_ETL"):
        self.dag_id = dag_id
        self.tasks: Dict[str, TaskNode] = {}

    def add_task(self, task: TaskNode, depends_on: Optional[List[str]] = None) -> None:
        """Registers task in DAG with optional list of upstream dependency task IDs."""
        self.tasks[task.task_id] = task
        if depends_on:
            for parent_id in depends_on:
                task.add_upstream(parent_id)

    def get_execution_order(self) -> List[str]:
        """Performs topological sort to determine valid task execution sequence."""
        in_degree = {task_id: len(task.upstream_tasks) for task_id, task in self.tasks.items()}
        queue = [task_id for task_id, deg in in_degree.items() if deg == 0]
        order = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for task_id, task in self.tasks.items():
                if curr in task.upstream_tasks:
                    in_degree[task_id] -= 1
                    if in_degree[task_id] == 0:
                        queue.append(task_id)

        if len(order) != len(self.tasks):
            raise ValueError("Circular dependency detected in PipelineDAG topological sort.")

        return order
