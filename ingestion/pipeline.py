"""
pipeline.py
-----------
Production-grade ETL Orchestration Pipeline for RetailLens (Phase 6 Complete).
Coordinates reading, schema validation, data cleaning, feature transformation,
watermark tracking, idempotent database loading, pipeline run audit tracking,
data lineage metadata recording, and automated data quality monitoring.
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
from ingestion.lineage import DataLineageTracker
from ingestion.loader import DatabaseLoader, LoadResult
from ingestion.quality_monitor import DataQualityMonitor, DataQualitySummary
from ingestion.reader import DataFileReader
from ingestion.tracker import PipelineRunTracker
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
    track_pipeline_runs: bool = True  # Set to True to record pipeline audit runs
    record_lineage: bool = True  # Set to True to record data lineage entries
    output_dir: str = "data/processed"
    target_table: str = "fact_sales"


@dataclass
class PipelineResult:
    """Encapsulates execution metadata, timing metrics, and row count statistics of a pipeline run."""
    run_id: str = ""
    status: str = "PENDING"  # SUCCESS, FAILED, PARTIAL, SKIPPED
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
    quality_summary: Optional[DataQualitySummary] = None
    output_file_path: Optional[str] = None
    error_message: Optional[str] = None


class ETLPipeline:
    """
    Central ETL Pipeline Orchestrator.
    Decoupled orchestrator injecting reader, validator, cleaner, transformer, loader, watermark, tracker, lineage, and quality dependencies.
    """

    def __init__(
        self,
        reader: Optional[DataFileReader] = None,
        validator: Optional[DataValidator] = None,
        cleaner: Optional[DataCleaner] = None,
        transformer: Optional[DataTransformer] = None,
        loader: Optional[DatabaseLoader] = None,
        watermark_mgr: Optional[WatermarkManager] = None,
        tracker: Optional[PipelineRunTracker] = None,
        lineage_tracker: Optional[DataLineageTracker] = None,
        quality_monitor: Optional[DataQualityMonitor] = None,
        config: Optional[PipelineConfig] = None,
    ):
        """Dependency Injection constructor allowing mock replacements in unit tests."""
        self.reader = reader or DataFileReader()
        self.validator = validator or DataValidator()
        self.cleaner = cleaner or DataCleaner()
        self.transformer = transformer or DataTransformer()
        self.loader = loader or DatabaseLoader()
        self.watermark_mgr = watermark_mgr or WatermarkManager()
        self.tracker = tracker or PipelineRunTracker()
        self.lineage_tracker = lineage_tracker or DataLineageTracker()
        self.quality_monitor = quality_monitor or DataQualityMonitor()
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

        run_id = ""
        try:
            # STAGE 0: Watermark & File Hash Inspection
            file_hash = self.watermark_mgr.compute_file_hash(file_path)
            result.file_hash = file_hash

            high_watermark_ts = None
            if self.config.incremental:
                high_watermark_ts = self.watermark_mgr.get_high_watermark_timestamp(self.config.target_table)

            if self.config.track_pipeline_runs:
                run_id = self.tracker.start_run(
                    source_file=file_path,
                    source_hash=file_hash,
                    pipeline_name=self.config.target_table,
                    watermark_before=high_watermark_ts,
                )
                result.run_id = run_id

            if self.config.check_watermark and self.watermark_mgr.is_file_processed(file_hash):
                logger.info("[STAGE: CHECK] File '%s' (Hash: %s...) was already processed. Idempotent check active.", Path(file_path).name, file_hash[:10])

            # STAGE 1: Data Extraction / Reading
            logger.info("[STAGE: READ] Reading dataset file...")
            df_raw = self.reader.read_file(file_path)
            result.total_rows_read = len(df_raw)

            # Incremental Watermark Filtering
            if self.config.incremental:
                logger.info("[STAGE: INCREMENTAL_FILTER] Filtering historical rows against high watermark...")
                df_raw, result.skipped_watermark_rows = self.watermark_mgr.filter_incremental_dataframe(
                    df_raw, high_watermark_ts, timestamp_col="InvoiceDate"
                )

            if df_raw.empty:
                logger.info("[STAGE: COMPLETE] No new records to process after incremental watermark filtering.")
                result.status = "SKIPPED" if result.skipped_watermark_rows > 0 else "SUCCESS"
                result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                result.duration_seconds = round(time.time() - start_ts, 3)

                if self.config.track_pipeline_runs and run_id:
                    self.tracker.complete_run(
                        run_id=run_id,
                        rows_read=result.total_rows_read,
                        rows_valid=0,
                        rows_invalid=0,
                        rows_transformed=0,
                        rows_inserted=0,
                        rows_skipped=result.skipped_watermark_rows,
                        watermark_after=high_watermark_ts,
                        execution_duration=result.duration_seconds,
                        status=result.status,
                    )
                return result

            # STAGE 2: Data Quality Validation
            df_valid = df_raw
            clean_stats = {}
            report = None
            if self.config.validate_data:
                logger.info("[STAGE: VALIDATE] Executing data quality validation...")
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
                    error_msg = f"Data validation failed! Valid: {report.valid_rows}, Invalid: {report.invalid_rows}"
                    logger.error(error_msg)
                    result.status = "FAILED"
                    result.error_message = error_msg
                    result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    result.duration_seconds = round(time.time() - start_ts, 3)

                    if self.config.track_pipeline_runs and run_id:
                        self.tracker.fail_run(run_id=run_id, error_message=error_msg, execution_duration=result.duration_seconds)
                    raise SchemaValidationError(error_msg)

            # STAGE 3: Data Cleaning
            df_clean = df_valid
            if self.config.clean_data:
                logger.info("[STAGE: CLEAN] Executing data cleaning and sanitization...")
                df_clean, clean_stats = self.cleaner.clean(df_valid)
                result.cleaned_rows = len(df_clean)

            # STAGE 4: Feature Transformation
            df_transformed = df_clean
            if self.config.transform_data:
                logger.info("[STAGE: TRANSFORM] Executing feature engineering transformations...")
                df_transformed = self.transformer.transform(df_clean)
                result.transformed_rows = len(df_transformed)

            # Save Processed Staging File
            os.makedirs(self.config.output_dir, exist_ok=True)
            output_filename = f"processed_{Path(file_path).stem}.csv"
            output_path = os.path.join(self.config.output_dir, output_filename)

            df_transformed.to_csv(output_path, index=False)
            result.output_file_path = output_path
            logger.info("Saved transformed dataset to: %s", output_path)

            # STAGE 5: Database Persistence Loading & Lineage Recording
            max_ts_val = high_watermark_ts
            if self.config.load_data:
                logger.info("[STAGE: LOAD] Executing database persistence loading...")
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

            # Compute Data Quality Summary Metrics
            quality_summary = self.quality_monitor.evaluate(
                run_id=run_id or "local-run",
                total_rows_read=result.total_rows_read,
                report=report,
                clean_stats=clean_stats,
                df_transformed=df_transformed,
                load_result=result.load_result,
                duration_seconds=result.duration_seconds,
            )
            result.quality_summary = quality_summary

            # Audit Run Tracking Completion
            if self.config.track_pipeline_runs and run_id:
                self.tracker.complete_run(
                    run_id=run_id,
                    rows_read=result.total_rows_read,
                    rows_valid=result.valid_rows,
                    rows_invalid=result.invalid_rows,
                    rows_transformed=result.transformed_rows,
                    rows_inserted=result.rows_loaded,
                    rows_skipped=result.skipped_watermark_rows,
                    watermark_after=max_ts_val,
                    execution_duration=result.duration_seconds,
                    status=result.status,
                )

            # Data Lineage Recording
            if self.config.record_lineage and run_id:
                self.lineage_tracker.record_lineage(
                    run_id=run_id,
                    source_file=file_path,
                    source_hash=file_hash,
                    source_row_count=result.total_rows_read,
                    target_table=self.config.target_table,
                    target_row_count=result.rows_loaded,
                    transformation_version="1.0.0",
                )

            logger.info("==================================================")
            logger.info("[STAGE: COMPLETE] ✅ Pipeline Completed Successfully in %.3f seconds", result.duration_seconds)
            logger.info("Summary: Read=%d | Skipped=%d | Valid=%d | Transformed=%d | Loaded=%d",
                        result.total_rows_read, result.skipped_watermark_rows, result.valid_rows, result.transformed_rows, result.rows_loaded)
            logger.info("==================================================")

            return result

        except Exception as e:
            logger.error("[STAGE: ERROR] Pipeline execution failed: %s", str(e), exc_info=True)
            result.status = "FAILED"
            result.error_message = str(e)
            result.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.duration_seconds = round(time.time() - start_ts, 3)

            if self.config.track_pipeline_runs and run_id:
                self.tracker.fail_run(run_id=run_id, error_message=str(e), execution_duration=result.duration_seconds)

            return result
