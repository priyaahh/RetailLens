"""
pipeline.py
-----------
Production-grade ETL Orchestration Pipeline for RetailLens.
Coordinates reading, schema validation, data cleaning, feature transformation,
and database persistence while tracking timing metrics, row execution statistics, and structured logging.
Follows SOLID principles (Single Responsibility, Open/Closed, Dependency Injection).
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from ingestion.cleaner import DataCleaner
from ingestion.loader import DatabaseLoader, LoadResult
from ingestion.reader import DataFileReader
from ingestion.transformer import DataTransformer
from ingestion.validator import DataValidator, SchemaValidationError, ValidationReport

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration-driven execution flags for ETL pipeline stages."""
    validate_data: bool = True
    clean_data: bool = True
    transform_data: bool = True
    load_data: bool = False  # Set to True to persist directly into PostgreSQL
    output_dir: str = "data/processed"
    target_table: str = "fact_sales"


@dataclass
class PipelineResult:
    """Encapsulates execution metadata, timing metrics, and row count statistics of a pipeline run."""
    status: str = "PENDING"  # SUCCESS, FAILED, PARTIAL_FAILURE
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    total_rows_read: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    cleaned_rows: int = 0
    transformed_rows: int = 0
    rows_loaded: int = 0
    validation_report: Optional[ValidationReport] = None
    load_result: Optional[LoadResult] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None


class ETLPipeline:
    """
    Central ETL Pipeline Orchestrator.
    Decoupled orchestrator injecting reader, validator, cleaner, transformer, and loader dependencies.
    """

    def __init__(
        self,
        reader: Optional[DataFileReader] = None,
        validator: Optional[DataValidator] = None,
        cleaner: Optional[DataCleaner] = None,
        transformer: Optional[DataTransformer] = None,
        loader: Optional[DatabaseLoader] = None,
        config: Optional[PipelineConfig] = None,
    ):
        """Dependency Injection constructor allowing mock replacements in unit tests."""
        self.reader = reader or DataFileReader()
        self.validator = validator or DataValidator()
        self.cleaner = cleaner or DataCleaner()
        self.transformer = transformer or DataTransformer()
        self.loader = loader or DatabaseLoader()
        self.config = config or PipelineConfig()

    def run(self, file_path: str) -> PipelineResult:
        """
        Executes end-to-end ETL pipeline for the given file path.

        :param file_path: Path to raw dataset file (CSV/Excel).
        :return: PipelineResult containing execution metrics and status.
        """
        start_ts = time.time()
        start_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = PipelineResult(
            status="RUNNING",
            start_time=start_str,
        )

        logger.info("==================================================")
        logger.info("🚀 Starting RetailLens ETL Pipeline Execution")
        logger.info("Target File: %s", file_path)
        logger.info("Configuration: %s", self.config)
        logger.info("==================================================")

        try:
            # -------------------------------------------------------------
            # Stage 1: Extraction / Reading
            # -------------------------------------------------------------
            logger.info("Stage 1/5: Executing File Extraction...")
            raw_df = self.reader.read_file(file_path)
            result.total_rows_read = len(raw_df)
            logger.info("Extract Stage Complete. Rows Read: %d", result.total_rows_read)

            current_df = raw_df

            # -------------------------------------------------------------
            # Stage 2: Schema & Data Quality Validation
            # -------------------------------------------------------------
            if self.config.validate_data:
                logger.info("Stage 2/5: Executing Schema & Data Quality Validation...")
                val_report, validated_df = self.validator.validate(current_df)
                result.validation_report = val_report
                result.valid_rows = val_report.valid_rows
                result.invalid_rows = val_report.invalid_rows
                current_df = validated_df
                logger.info(
                    "Validation Stage Complete. Valid Rows: %d | Invalid Rows: %d",
                    result.valid_rows,
                    result.invalid_rows,
                )
            else:
                logger.info("Stage 2/5: Validation bypassed by configuration.")
                result.valid_rows = len(current_df)

            # -------------------------------------------------------------
            # Stage 3: Data Cleaning & Deduplication
            # -------------------------------------------------------------
            if self.config.clean_data:
                logger.info("Stage 3/5: Executing Data Cleaning & Imputation...")
                cleaned_df, clean_stats = self.cleaner.clean(current_df)
                result.cleaned_rows = len(cleaned_df)
                current_df = cleaned_df
                logger.info("Cleaning Stage Complete. Output Rows: %d", result.cleaned_rows)
            else:
                logger.info("Stage 3/5: Cleaning bypassed by configuration.")
                result.cleaned_rows = len(current_df)

            # -------------------------------------------------------------
            # Stage 4: Feature Engineering & Transformation
            # -------------------------------------------------------------
            if self.config.transform_data:
                logger.info("Stage 4/5: Executing Feature Transformations...")
                transformed_df = self.transformer.transform(current_df)
                result.transformed_rows = len(transformed_df)
                current_df = transformed_df
                logger.info("Transformation Stage Complete. Final Features: %d", len(current_df.columns))
            else:
                logger.info("Stage 4/5: Transformation bypassed by configuration.")
                result.transformed_rows = len(current_df)

            # -------------------------------------------------------------
            # Stage 5: Database Bulk Persistence & Staging Save
            # -------------------------------------------------------------
            os.makedirs(self.config.output_dir, exist_ok=True)
            input_filename = Path(file_path).stem
            output_path = os.path.join(self.config.output_dir, f"processed_{input_filename}.csv")
            current_df.to_csv(output_path, index=False)
            result.output_file_path = output_path
            logger.info("Saved processed staging dataset to: %s", output_path)

            if self.config.load_data:
                logger.info("Stage 5/5: Persisting processed data into PostgreSQL table '%s'...", self.config.target_table)
                load_res = self.loader.load(current_df, table_name=self.config.target_table)
                result.load_result = load_res
                result.rows_loaded = load_res.rows_inserted
                if load_res.status == "FAILED":
                    raise Exception(load_res.error_message)

            # Mark Status
            result.status = "SUCCESS"

        except SchemaValidationError as e:
            error_msg = f"Pipeline halted due to critical schema failure: {str(e)}"
            logger.error(error_msg)
            result.status = "FAILED"
            result.error_message = error_msg

        except Exception as e:
            error_msg = f"Pipeline execution failed unexpectedly: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.status = "FAILED"
            result.error_message = error_msg

        finally:
            end_ts = time.time()
            result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.duration_seconds = round(end_ts - start_ts, 4)

            logger.info("==================================================")
            logger.info("📊 Pipeline Execution Summary")
            logger.info("Status: %s", result.status)
            logger.info("Duration: %.4f seconds", result.duration_seconds)
            logger.info("Total Rows Read: %d", result.total_rows_read)
            logger.info("Transformed Rows: %d", result.transformed_rows)
            logger.info("Rows Loaded to DB: %d", result.rows_loaded)
            logger.info("Output Destination: %s", result.output_file_path)
            logger.info("==================================================")

        return result
