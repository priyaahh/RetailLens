"""
pipeline.py
-----------
Production-grade ETL Orchestration Pipeline for RetailLens.
Coordinates reading, schema validation, data cleaning, feature transformation,
and database persistence while tracking timing metrics, row execution statistics, structured logging,
watermark tracking, and idempotent execution.
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
from ingestion.watermark import WatermarkManager

# Configure module logger
logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Configuration-driven execution flags for ETL pipeline stages."""
    validate_data: bool = True
    clean_data: bool = True
    transform_data: bool = True
    load_data: bool = False  # Set to True to persist directly into PostgreSQL
    incremental: bool = True  # Set to True for watermark-based incremental loading
    check_watermark: bool = True  # Set to True to check file hashes for idempotency
    output_dir: str = "data/processed"
    target_table: str = "fact_sales"


@dataclass
class PipelineResult:
    """Encapsulates execution metadata, timing metrics, and row count statistics of a pipeline run."""
    status: str = "PENDING"  # SUCCESS, FAILED, PARTIAL_FAILURE
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    file_hash: str = ""
    total_rows_read: int = 0
    skipped_watermark_rows: int = 0
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
    Decoupled orchestrator injecting reader, validator, cleaner, transformer, loader, and watermark dependencies.
    """

    def __init__(
        self,
        reader: Optional[DataFileReader] = None,
        validator: Optional[DataValidator] = None,
        cleaner: Optional[DataCleaner] = None,
        transformer: Optional[DataTransformer] = None,
        loader: Optional[DatabaseLoader] = None,
        watermark_mgr: Optional[WatermarkManager] = None,
        config: Optional[PipelineConfig] = None,
    ):
        """Dependency Injection constructor allowing mock replacements in unit tests."""
        self.reader = reader or DataFileReader()
        self.validator = validator or DataValidator()
        self.cleaner = cleaner or DataCleaner()
        self.transformer = transformer or DataTransformer()
        self.loader = loader or DatabaseLoader()
        self.watermark_mgr = watermark_mgr or WatermarkManager()
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
        logger.info("==================================================")

        try:
            # 0. Watermark & File Hash Inspection
            file_hash = self.watermark_mgr.compute_file_hash(file_path)
            result.file_hash = file_hash

            if self.config.check_watermark and self.watermark_mgr.is_file_processed(file_hash):
                logger.info("File '%s' (Hash: %s...) was already processed. Idempotent check active.", Path(file_path).name, file_hash[:10])

            # STAGE 1: Data Extraction / Reading
            logger.info("Stage 1: Reading dataset file...")
            df_raw = self.reader.read_file(file_path)
            result.total_rows_read = len(df_raw)

            # Incremental Watermark Filtering
            high_watermark_ts = None
            if self.config.incremental:
                high_watermark_ts = self.watermark_mgr.get_high_watermark_timestamp(self.config.target_table)
                df_raw, result.skipped_watermark_rows = self.watermark_mgr.filter_incremental_dataframe(
                    df_raw, high_watermark_ts, timestamp_col="InvoiceDate"
                )

            if df_raw.empty:
                logger.info("No new records to process after incremental watermark filtering.")
                result.status = "SUCCESS"
                result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result.duration_seconds = round(time.time() - start_ts, 3)
                return result

            # STAGE 2: Data Validation
            df_valid = df_raw
            if self.config.validate_data:
                logger.info("Stage 2: Executing data quality validation...")
                val_output = self.validator.validate(df_raw)
                if isinstance(val_output, tuple):
                    report, df_valid = val_output
                else:
                    report = val_output
                    df_valid = df_raw

                result.validation_report = report
                result.valid_rows = report.valid_rows
                result.invalid_rows = report.invalid_rows

                if not report.is_valid:
                    error_msg = f"Data validation failed! Passed: {report.valid_rows}, Failed: {report.invalid_rows}"
                    logger.error(error_msg)
                    result.status = "FAILED"
                    result.error_message = error_msg
                    result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    result.duration_seconds = round(time.time() - start_ts, 3)
                    raise SchemaValidationError(error_msg)

            # STAGE 3: Data Cleaning
            df_clean = df_valid
            if self.config.clean_data:
                logger.info("Stage 3: Executing data cleaning and sanitization...")
                df_clean, clean_stats = self.cleaner.clean(df_valid)
                result.cleaned_rows = len(df_clean)

            # STAGE 4: Feature Transformation
            df_transformed = df_clean
            if self.config.transform_data:
                logger.info("Stage 4: Executing feature engineering transformations...")
                df_transformed = self.transformer.transform(df_clean)
                result.transformed_rows = len(df_transformed)

            # STAGE 5: Save Processed File & Load into Database
            os.makedirs(self.config.output_dir, exist_ok=True)
            output_filename = f"processed_{Path(file_path).stem}.csv"
            output_path = os.path.join(self.config.output_dir, output_filename)

            df_transformed.to_csv(output_path, index=False)
            result.output_file_path = output_path
            logger.info("Saved transformed dataset to: %s", output_path)

            if self.config.load_data:
                logger.info("Stage 5: Executing database persistence loading...")
                load_res = self.loader.load(
                    df_transformed, table_name=self.config.target_table, if_exists="append", idempotent=True
                )
                result.load_result = load_res
                result.rows_loaded = load_res.rows_inserted

                # Record Watermark Entry
                max_file_ts = pd.to_datetime(df_transformed["InvoiceDate"]).max() if "InvoiceDate" in df_transformed.columns else None
                max_ts_val = max_file_ts.to_pydatetime() if pd.notna(max_file_ts) else high_watermark_ts
                self.watermark_mgr.record_watermark(
                    file_path=file_path,
                    file_hash=file_hash,
                    high_watermark_ts=max_ts_val,
                    rows_processed=result.rows_loaded,
                )

            result.status = "SUCCESS"
            result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.duration_seconds = round(time.time() - start_ts, 3)

            logger.info("==================================================")
            logger.info("✅ Pipeline Completed Successfully in %.3f seconds", result.duration_seconds)
            logger.info("Summary: Read=%d | Skipped=%d | Valid=%d | Transformed=%d | Loaded=%d",
                        result.total_rows_read, result.skipped_watermark_rows, result.valid_rows, result.transformed_rows, result.rows_loaded)
            logger.info("==================================================")

            return result

        except Exception as e:
            logger.error("Pipeline execution failed: %s", str(e), exc_info=True)
            result.status = "FAILED"
            result.error_message = str(e)
            result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.duration_seconds = round(time.time() - start_ts, 3)
            return result
