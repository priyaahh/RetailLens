"""
validator.py
------------
Production-grade schema and data quality validation engine for RetailLens.
Performs structural schema checks, data type validations, and business rule assertions,
returning a structured ValidationReport dataclass.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Set, Tuple

import pandas as pd

from config.schema_config import IngestionConfig

# Configure module-level logger
logger = logging.getLogger(__name__)


# Custom Exception Hierarchy
class ValidationException(Exception):
    """Base exception class for validation errors."""
    pass


class SchemaValidationError(ValidationException):
    """Raised when structural schema checks fail."""
    pass


class BusinessRuleValidationError(ValidationException):
    """Raised when critical business logic rules fail."""
    pass


@dataclass
class ValidationReport:
    """Structured container holding execution metrics and error breakdowns of a dataset validation run."""
    total_rows: int = 0
    valid_rows: int = 0
    invalid_rows: int = 0
    is_valid: bool = True
    error_counts: Dict[str, int] = field(default_factory=dict)
    error_summary: List[str] = field(default_factory=list)

    def add_error(self, category: str, count: int, message: str) -> None:
        """Helper to register validation errors in summary statistics."""
        self.error_counts[category] = self.error_counts.get(category, 0) + count
        self.error_summary.append(f"[{category}] {message} (Affected Rows: {count})")
        if count > 0:
            self.invalid_rows = min(self.total_rows, self.invalid_rows + count)

    def finalize(self) -> None:
        """Calculates final valid row count and overall validity state."""
        self.valid_rows = max(0, self.total_rows - self.invalid_rows)
        self.is_valid = len(self.error_counts) == 0 or self.invalid_rows == 0

    @property
    def passed_rows(self) -> int:
        """Alias for valid_rows metric."""
        return self.valid_rows

    @property
    def failed_rows(self) -> int:
        """Alias for invalid_rows metric."""
        return self.invalid_rows


class DataValidator:
    """Modular Data Quality Engine performing structural and semantic dataset checks."""

    def __init__(self, config: IngestionConfig = IngestionConfig()):
        self.config = config

    def validate(self, df: pd.DataFrame) -> Tuple[ValidationReport, pd.DataFrame]:
        """
        Executes complete validation suite against the input DataFrame.

        :param df: Loaded Pandas DataFrame from ingestion reader.
        :return: Tuple containing (ValidationReport, Flagged/Validated DataFrame).
        :raises SchemaValidationError: If structural schema is severely broken (empty df, missing columns).
        """
        logger.info("Starting data quality validation run...")
        report = ValidationReport(total_rows=len(df))

        # 1. Structural Schema Validation
        self._validate_schema_structure(df, report)

        # 2. Data Type & Format Validation
        validated_df = self._validate_types_and_formats(df.copy(), report)

        # 3. Business Rule Validation
        self._validate_business_rules(validated_df, report)

        report.finalize()
        logger.info(
            "Validation complete. Total Rows: %d | Valid: %d | Invalid: %d | Quality Score: %.2f%%",
            report.total_rows,
            report.valid_rows,
            report.invalid_rows,
            (report.valid_rows / report.total_rows * 100) if report.total_rows > 0 else 0.0,
        )

        return report, validated_df

    def _validate_schema_structure(self, df: pd.DataFrame, report: ValidationReport) -> None:
        """Asserts DataFrame is non-empty, contains no duplicate columns, and has required headers."""
        if df.empty:
            logger.error("Empty dataset detected!")
            report.add_error("EMPTY_DATASET", 0, "Dataset contains zero rows.")
            raise SchemaValidationError("Uploaded dataset is empty.")

        # Duplicate column names check
        duplicated_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicated_cols:
            msg = f"Duplicate column headers found: {duplicated_cols}"
            logger.error(msg)
            report.add_error("DUPLICATE_COLUMNS", 0, msg)
            raise SchemaValidationError(msg)

        # Missing required columns check
        missing_cols = [col for col in self.config.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns in dataset: {missing_cols}"
            logger.error(msg)
            report.add_error("MISSING_REQUIRED_COLUMNS", 0, msg)
            raise SchemaValidationError(msg)

        # Unexpected extra columns warning log
        expected_set: Set[str] = set(self.config.EXPECTED_COLUMNS)
        unexpected_cols = [col for col in df.columns if col not in expected_set]
        if unexpected_cols:
            logger.warning("Dataset contains unexpected extra columns: %s", unexpected_cols)

    def _validate_types_and_formats(self, df: pd.DataFrame, report: ValidationReport) -> pd.DataFrame:
        """Parses and validates column data types (Datetime, Numeric, String)."""
        # Validate Datetime Parsing
        if "InvoiceDate" in df.columns:
            invalid_dates = pd.to_datetime(df["InvoiceDate"], errors="coerce").isna()
            invalid_date_count = invalid_dates.sum()
            if invalid_date_count > 0:
                logger.warning("Found %d rows with unparseable InvoiceDate values.", invalid_date_count)
                report.add_error("INVALID_DATE_FORMAT", invalid_date_count, "InvoiceDate string could not be parsed as Datetime.")

        # Validate Numeric Types
        for num_col in ["Quantity", "UnitPrice"]:
            if num_col in df.columns:
                non_numeric = pd.to_numeric(df[num_col], errors="coerce").isna() & df[num_col].notna()
                non_numeric_count = non_numeric.sum()
                if non_numeric_count > 0:
                    logger.warning("Found %d non-numeric values in column '%s'.", non_numeric_count, num_col)
                    report.add_error(
                        "INVALID_NUMERIC_TYPE",
                        non_numeric_count,
                        f"Non-numeric values found in '{num_col}'.",
                    )

        return df

    def _validate_business_rules(self, df: pd.DataFrame, report: ValidationReport) -> None:
        """Verifies domain business logic rules (Negative price, future dates, missing invoice IDs)."""
        # Rule 1: Missing Invoice Numbers
        if "InvoiceNo" in df.columns:
            missing_invoices = df["InvoiceNo"].isna() | (df["InvoiceNo"].astype(str).str.strip() == "")
            missing_invoice_count = missing_invoices.sum()
            if missing_invoice_count > 0:
                logger.warning("Found %d rows missing InvoiceNo identifier.", missing_invoice_count)
                report.add_error("MISSING_INVOICE_NO", missing_invoice_count, "InvoiceNo primary business identifier is missing.")

        # Rule 2: Negative Unit Prices (Data Anomaly)
        if "UnitPrice" in df.columns:
            numeric_prices = pd.to_numeric(df["UnitPrice"], errors="coerce")
            negative_prices = numeric_prices < 0
            neg_price_count = negative_prices.sum()
            if neg_price_count > 0:
                logger.warning("Found %d rows with negative UnitPrice (< 0.00).", neg_price_count)
                report.add_error("NEGATIVE_UNIT_PRICE", neg_price_count, "UnitPrice cannot be negative.")

        # Rule 3: Future Invoice Dates
        if "InvoiceDate" in df.columns:
            parsed_dates = pd.to_datetime(df["InvoiceDate"], errors="coerce")
            future_dates = parsed_dates > datetime.now()
            future_date_count = future_dates.sum()
            if future_date_count > 0:
                logger.warning("Found %d rows with future InvoiceDate timestamps.", future_date_count)
                report.add_error("FUTURE_INVOICE_DATE", future_date_count, "InvoiceDate occurs in the future.")

        # Rule 4: Negative Quantities (Order Cancellations flag log)
        if "Quantity" in df.columns:
            numeric_qty = pd.to_numeric(df["Quantity"], errors="coerce")
            cancellations = numeric_qty < 0
            cancel_count = cancellations.sum()
            if cancel_count > 0:
                logger.info("Detected %d return/cancellation transactions (Quantity < 0).", cancel_count)
