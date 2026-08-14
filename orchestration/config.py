"""
config.py
---------
Production Workflow Orchestration Configuration for RetailLens (Phase 8 Milestone 9).
"""

from dataclasses import dataclass


@dataclass
class ProductionDAGConfig:
    """Configuration settings for production DAG task execution."""
    dag_id: str = "retaillens_production_etl_dag"
    schedule_interval: str = "0 2 * * *"  # Daily at 02:00 AM UTC
    max_active_runs: int = 1
    catchup: bool = False
    default_retries: int = 3
    retry_delay_seconds: int = 60
    execution_timeout_seconds: int = 3600
