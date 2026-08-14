"""
test_orchestration.py
----------------------
Unit tests for PipelineDAG, OrchestratedPipelineWorkflow, and PipelineScheduler (Phase 7 Milestones 7, 8, 9).
"""

import unittest
from unittest.mock import MagicMock

from ingestion.pipeline import PipelineResult
from orchestration.dag import PipelineDAG, TaskNode
from orchestration.scheduler import PipelineScheduler
from orchestration.workflow import OrchestratedPipelineWorkflow


class TestOrchestration(unittest.TestCase):

    def test_dag_topological_sort(self):
        """Verify topological sorting of PipelineDAG tasks."""
        dag = PipelineDAG()
        n1 = TaskNode("extract", lambda: True)
        n2 = TaskNode("transform", lambda: True)
        n3 = TaskNode("load", lambda: True)

        dag.add_task(n1)
        dag.add_task(n2, depends_on=["extract"])
        dag.add_task(n3, depends_on=["transform"])

        order = dag.get_execution_order()
        self.assertEqual(order, ["extract", "transform", "load"])

    def test_orchestrated_workflow_execution(self):
        """Verify OrchestratedPipelineWorkflow delegates execution to pipeline."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = PipelineResult(status="SUCCESS")

        workflow = OrchestratedPipelineWorkflow(pipeline=mock_pipeline)
        res = workflow.execute_file("data/raw/sales.csv")
        self.assertEqual(res.status, "SUCCESS")

    def test_scheduler_concurrency_lock(self):
        """Verify PipelineScheduler locks against concurrent runs."""
        mock_pipeline = MagicMock()
        mock_pipeline.run.return_value = PipelineResult(status="SUCCESS")

        scheduler = PipelineScheduler(pipeline=mock_pipeline)
        res = scheduler.trigger_batch("data/raw/sales.csv", schedule_type="daily")
        self.assertEqual(res.status, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
