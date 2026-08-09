"""
cleaner.py
----------
Production-grade data cleaning engine for RetailLens.
Handles null value imputation, whitespace trimming, string casing normalization,
impossible value filtering, and safe type conversions.
"""

import logging
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaner:
    """Data Cleaning Engine providing idempotent vector cleaning routines."""

    def clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """
        Executes complete cleaning pipeline on input DataFrame.

        :param df: Validated input DataFrame.
        :return: Tuple containing (Cleaned DataFrame, Cleaning Statistics Dict).
        """
        logger.info("Starting data cleaning pipeline execution...")
        initial_row_count = len(df)
        cleaned_df = df.copy()

        stats = {
            "initial_rows": initial_row_count,
            "duplicates_removed": 0,
            "invalid_prices_removed": 0,
            "nulls_imputed": 0,
            "final_rows": 0,
        }

        # 1. Strip Whitespace & Normalize String Casing
        cleaned_df = self._clean_string_fields(cleaned_df)

        # 2. Handle Impossible / Invalid Data Records
        cleaned_df, stats["invalid_prices_removed"] = self._remove_invalid_records(cleaned_df)

        # 3. Impute Missing Values
        cleaned_df, stats["nulls_imputed"] = self._impute_missing_values(cleaned_df)

        # 4. Remove Duplicate Rows
        cleaned_df, stats["duplicates_removed"] = self._remove_duplicates(cleaned_df)

        # 5. Enforce Standardized Data Types
        cleaned_df = self._cast_data_types(cleaned_df)

        stats["final_rows"] = len(cleaned_df)
        logger.info(
            "Data cleaning complete. Initial Rows: %d | Final Rows: %d | Duplicates Removed: %d | Invalid Removed: %d",
            stats["initial_rows"],
            stats["final_rows"],
            stats["duplicates_removed"],
            stats["invalid_prices_removed"],
        )

        return cleaned_df, stats

    def _clean_string_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trims leading/trailing whitespace and normalizes text casing."""
        string_cols = df.select_dtypes(include=["object", "string"]).columns

        for col in string_cols:
            df[col] = df[col].astype(str).str.strip()

        # Specific normalization: Uppercase StockCode & InvoiceNo, Title Case Country
        if "StockCode" in df.columns:
            df["StockCode"] = df["StockCode"].str.upper()
        if "InvoiceNo" in df.columns:
            df["InvoiceNo"] = df["InvoiceNo"].str.upper()
        if "Country" in df.columns:
            df["Country"] = df["Country"].str.title()

        return df

    def _remove_invalid_records(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Removes records with impossible values (e.g. UnitPrice < 0.00 or missing critical InvoiceNo)."""
        initial_len = len(df)

        # Filter out negative UnitPrice
        if "UnitPrice" in df.columns:
            df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
            df = df[df["UnitPrice"] >= 0.0]

        # Filter out empty or missing InvoiceNo
        if "InvoiceNo" in df.columns:
            df = df[df["InvoiceNo"].notna() & (df["InvoiceNo"] != "") & (df["InvoiceNo"] != "NAN")]

        removed_count = initial_len - len(df)
        if removed_count > 0:
            logger.info("Removed %d records with impossible/invalid values.", removed_count)
        return df, removed_count

    def _impute_missing_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Imputes missing CustomerID as 'GUEST' and missing Description as 'UNKNOWN'."""
        imputed_count = 0

        if "CustomerID" in df.columns:
            null_cust = df["CustomerID"].isna() | (df["CustomerID"] == "") | (df["CustomerID"] == "NAN") | (df["CustomerID"] == "NONE")
            imputed_count += null_cust.sum()
            df.loc[null_cust, "CustomerID"] = "GUEST"

        if "Description" in df.columns:
            null_desc = df["Description"].isna() | (df["Description"] == "") | (df["Description"] == "NAN")
            imputed_count += null_desc.sum()
            df.loc[null_desc, "Description"] = "UNKNOWN DESCRIPTION"

        if imputed_count > 0:
            logger.info("Imputed %d missing field values.", imputed_count)

        return df, imputed_count

    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Identifies and drops exact duplicate rows across all primary business fields."""
        initial_count = len(df)

        subset_cols = [col for col in ["InvoiceNo", "StockCode", "Quantity", "InvoiceDate", "CustomerID"] if col in df.columns]

        if subset_cols:
            df = df.drop_duplicates(subset=subset_cols, keep="first")
        else:
            df = df.drop_duplicates(keep="first")

        removed_duplicates = initial_count - len(df)
        if removed_duplicates > 0:
            logger.info("Dropped %d exact duplicate row records.", removed_duplicates)

        return df, removed_duplicates

    def _cast_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Converts columns safely to their explicit production data types."""
        if "Quantity" in df.columns:
            df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0).astype("int64")

        if "UnitPrice" in df.columns:
            df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce").fillna(0.0).astype("float64")

        if "InvoiceDate" in df.columns:
            df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

        return df
