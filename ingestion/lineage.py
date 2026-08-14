"""
lineage.py
----------
Data Lineage Metadata Engine for RetailLens (Phase 6 Milestone 3).
Provides end-to-end data provenance tracing from source tabular files through ETL transformation
to target PostgreSQL analytical tables.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class DataLineageTracker:
    """Manages source-to-target data lineage audit records in the data_lineage database table."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        self.engine = engine or get_db_engine()

    def record_lineage(
        self,
        run_id: str,
        source_file: str,
        source_hash: str,
        source_row_count: int,
        target_table: str = "fact_sales",
        target_row_count: int = 0,
        transformation_version: str = "1.0.0",
    ) -> bool:
        """
        Records source-to-target lineage entry linked to a pipeline run.

        :param run_id: Pipeline execution run ID UUID string.
        :param source_file: Target raw dataset file path.
        :param source_hash: SHA-256 digest of input data file.
        :param source_row_count: Total raw records extracted.
        :param target_table: Destination database table name.
        :param target_row_count: Records persisted to destination table.
        :param transformation_version: Pipeline transformation version code.
        :return: True on success.
        """
        query = """
            INSERT INTO data_lineage (
                run_id, source_file, source_hash, source_row_count,
                target_table, target_row_count, transformation_version, created_at
            ) VALUES (
                :run_id, :source_file, :source_hash, :source_row_count,
                :target_table, :target_row_count, :transformation_version, :created_at
            );
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {
                        "run_id": run_id,
                        "source_file": str(source_file),
                        "source_hash": source_hash,
                        "source_row_count": source_row_count,
                        "target_table": target_table,
                        "target_row_count": target_row_count,
                        "transformation_version": transformation_version,
                        "created_at": datetime.now(),
                    },
                )
            logger.info("Recorded data lineage for run '%s' -> table '%s' (%d rows)", run_id, target_table, target_row_count)
            return True
        except Exception as e:
            logger.warning("Could not record data lineage entry: %s", str(e))
            return False

    def get_lineage_by_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves data lineage records for a given run_id.

        :param run_id: Pipeline run UUID string.
        :return: List of lineage record dictionaries.
        """
        query = "SELECT * FROM data_lineage WHERE run_id = :run_id ORDER BY created_at DESC;"
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(text(query), {"run_id": run_id}).mappings().all()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Failed to retrieve lineage for run '%s': %s", run_id, str(e))
            return []

    def get_lineage_for_file(self, source_file: str) -> List[Dict[str, Any]]:
        """
        Retrieves all data lineage records for a specific source file path.

        :param source_file: Source file path string.
        :return: List of lineage record dictionaries.
        """
        query = "SELECT * FROM data_lineage WHERE source_file = :source_file ORDER BY created_at DESC;"
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(text(query), {"source_file": str(source_file)}).mappings().all()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Failed to retrieve lineage for file '%s': %s", source_file, str(e))
            return []
