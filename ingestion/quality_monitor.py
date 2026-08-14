"""
quality_monitor.py
------------------
Data Quality Monitoring & Performance Metrics Engine for RetailLens (Phase 6 Milestones 5 & 7).
Calculates automated quality scores, null imputation rates, duplicate skip rates, processing speed,
and anomaly thresholds per pipeline execution run.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd

from ingestion.loader import LoadResult
from ingestion.validator import ValidationReport

logger = logging.getLogger(__name__)


@dataclass
class DataQualitySummary:
    """Encapsulates data quality metrics, quality scores, and operational throughput statistics."""
    run_id: str = ""
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    data_quality_score_pct: float = 100.0
    null_imputed_count: int = 0
    duplicate_removed_count: int = 0
    invalid_price_count: int = 0
    cancellation_count: int = 0
    guest_customer_count: int = 0
    records_per_second: float = 0.0
    duplicate_skip_rate_pct: float = 0.0
    threshold_status: str = "PASS"  # PASS, WARNING, CRITICAL
    alert_messages: list = field(default_factory=list)


class DataQualityMonitor:
    """Evaluates data quality metrics and performance throughput for pipeline runs."""

    def __init__(
        self,
        invalid_row_warning_threshold: float = 5.0,     # Warning if invalid rows > 5%
        invalid_row_critical_threshold: float = 15.0,   # Critical if invalid rows > 15%
    ):
        self.invalid_row_warning_threshold = invalid_row_warning_threshold
        self.invalid_row_critical_threshold = invalid_row_critical_threshold

    def evaluate(
        self,
        run_id: str,
        total_rows_read: int,
        report: Optional[ValidationReport] = None,
        clean_stats: Optional[Dict[str, int]] = None,
        df_transformed: Optional[pd.DataFrame] = None,
        load_result: Optional[LoadResult] = None,
        duration_seconds: float = 0.0,
    ) -> DataQualitySummary:
        """
        Computes structured DataQualitySummary object from execution stage outputs.

        :param run_id: Pipeline execution run ID UUID.
        :param total_rows_read: Total raw rows extracted.
        :param report: ValidationReport from DataValidator.
        :param clean_stats: Cleaning statistics dict from DataCleaner.
        :param df_transformed: Transformed DataFrame.
        :param load_result: LoadResult from DatabaseLoader.
        :param duration_seconds: Pipeline execution duration in seconds.
        :return: Populated DataQualitySummary object.
        """
        summary = DataQualitySummary(run_id=run_id, total_rows=total_rows_read)

        if report:
            summary.valid_rows = report.valid_rows
            summary.invalid_rows = report.invalid_rows
            if total_rows_read > 0:
                summary.data_quality_score_pct = round((report.valid_rows / total_rows_read) * 100, 2)

        if clean_stats:
            summary.null_imputed_count = clean_stats.get("nulls_imputed", 0)
            summary.duplicate_removed_count = clean_stats.get("duplicates_removed", 0)
            summary.invalid_price_count = clean_stats.get("invalid_prices_removed", 0)

        if df_transformed is not None and not df_transformed.empty:
            if "IsCancellation" in df_transformed.columns:
                summary.cancellation_count = int(df_transformed["IsCancellation"].sum())
            elif "is_cancellation" in df_transformed.columns:
                summary.cancellation_count = int(df_transformed["is_cancellation"].sum())

            if "CustomerType" in df_transformed.columns:
                summary.guest_customer_count = int((df_transformed["CustomerType"] == "Guest").sum())
            elif "customer_type" in df_transformed.columns:
                summary.guest_customer_count = int((df_transformed["customer_type"] == "Guest").sum())

        if load_result:
            if total_rows_read > 0 and load_result.rows_skipped_duplicate > 0:
                summary.duplicate_skip_rate_pct = round((load_result.rows_skipped_duplicate / total_rows_read) * 100, 2)

        if duration_seconds > 0:
            summary.records_per_second = round(total_rows_read / duration_seconds, 2)

        # Evaluate Data Quality Threshold Badges
        invalid_pct = (summary.invalid_rows / total_rows_read * 100) if total_rows_read > 0 else 0.0
        if invalid_pct >= self.invalid_row_critical_threshold:
            summary.threshold_status = "CRITICAL"
            summary.alert_messages.append(f"High invalid row rate detected: {invalid_pct:.1f}% (Threshold: {self.invalid_row_critical_threshold}%)")
        elif invalid_pct >= self.invalid_row_warning_threshold:
            summary.threshold_status = "WARNING"
            summary.alert_messages.append(f"Elevated invalid row rate: {invalid_pct:.1f}% (Threshold: {self.invalid_row_warning_threshold}%)")

        logger.info(
            "Data Quality Monitor evaluated run '%s': Score=%.2f%% | Speed=%.1f rec/s | Status=%s",
            run_id,
            summary.data_quality_score_pct,
            summary.records_per_second,
            summary.threshold_status,
        )
        return summary
