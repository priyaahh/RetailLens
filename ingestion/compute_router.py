"""
compute_router.py
------------------
Hybrid Compute Engine Router for RetailLens (Phase 7 Milestone 3).
Evaluates dataset file size and configuration settings to dynamically select between
single-node Pandas execution and distributed PySpark execution.
"""

import logging
import os
from typing import Optional, Tuple

from config.app_config import get_config
from ingestion.spark_transformer import HAS_SPARK, SparkDataTransformer
from ingestion.transformer import DataTransformer

logger = logging.getLogger(__name__)


class ComputeRouter:
    """Dynamic Compute Router selecting between Pandas and PySpark compute engines."""

    def __init__(
        self,
        default_engine: Optional[str] = None,
        spark_threshold_mb: Optional[float] = None,
    ):
        """
        Constructor configuring engine parameters and file size boundaries.

        :param default_engine: Engine choice string ('auto', 'pandas', 'spark').
        :param spark_threshold_mb: File size threshold in megabytes to trigger PySpark.
        """
        app_cfg = get_config()
        self.default_engine = (default_engine or os.getenv("PROCESSING_ENGINE", "auto")).lower()
        self.spark_threshold_mb = spark_threshold_mb or float(os.getenv("SPARK_THRESHOLD_MB", "100"))

        if self.default_engine not in ["auto", "pandas", "spark"]:
            logger.warning("Invalid PROCESSING_ENGINE '%s'. Defaulting to 'auto'.", self.default_engine)
            self.default_engine = "auto"

    def select_engine(self, file_path: str, engine_override: Optional[str] = None) -> Tuple[str, float]:
        """
        Determines the optimal compute engine ('pandas' or 'spark') based on file size and rules.

        :param file_path: Target input dataset file path.
        :param engine_override: Optional explicit engine selection ('pandas' or 'spark').
        :return: Tuple of (selected_engine_name, file_size_mb).
        """
        file_size_mb = 0.0
        if os.path.exists(file_path):
            file_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)

        target_mode = (engine_override or self.default_engine).lower()

        if target_mode == "pandas":
            logger.info("[ROUTER] Selected engine: PANDAS (Explicit setting | Size: %.2fMB)", file_size_mb)
            return "pandas", file_size_mb

        if target_mode == "spark":
            if HAS_SPARK:
                logger.info("[ROUTER] Selected engine: SPARK (Explicit setting | Size: %.2fMB)", file_size_mb)
                return "spark", file_size_mb
            else:
                logger.warning("[ROUTER] PySpark requested but unavailable. Falling back to PANDAS.")
                return "pandas", file_size_mb

        # AUTO mode selection based on file size threshold
        if file_size_mb >= self.spark_threshold_mb and HAS_SPARK:
            logger.info(
                "[ROUTER] Selected engine: SPARK (Auto threshold triggered | Size: %.2fMB >= Threshold: %.2fMB)",
                file_size_mb,
                self.spark_threshold_mb,
            )
            return "spark", file_size_mb

        logger.info(
            "[ROUTER] Selected engine: PANDAS (Auto mode | Size: %.2fMB < Threshold: %.2fMB)",
            file_size_mb,
            self.spark_threshold_mb,
        )
        return "pandas", file_size_mb

    def get_transformer(self, engine_name: str) -> object:
        """
        Instantiates appropriate transformer class instance.

        :param engine_name: Engine choice string ('pandas' or 'spark').
        :return: DataTransformer or SparkDataTransformer instance.
        """
        if engine_name.lower() == "spark" and HAS_SPARK:
            return SparkDataTransformer()
        return DataTransformer()
