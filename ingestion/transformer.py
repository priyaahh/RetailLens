"""
transformer.py
--------------
Production-grade data transformation and feature engineering engine for RetailLens.
Enriches clean tabular datasets with temporal attributes, revenue calculations,
cancellation flags, customer categories, and analytical segmentation buckets.
"""

import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataTransformer:
    """Data Transformation & Feature Engineering Engine."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Executes feature engineering transformations on cleaned DataFrame.

        :param df: Cleaned Pandas DataFrame.
        :return: Transformed & Enriched DataFrame.
        """
        logger.info("Starting feature engineering transformations...")
        transformed_df = df.copy()

        # 1. Total Line Item Amount (TotalPrice)
        transformed_df = self._add_total_price(transformed_df)

        # 2. Temporal Feature Extraction
        transformed_df = self._add_temporal_features(transformed_df)

        # 3. Order Cancellation Flag
        transformed_df = self._add_cancellation_flag(transformed_df)

        # 4. Customer Type Categorization
        transformed_df = self._add_customer_type(transformed_df)

        # 5. Revenue Segmentation Buckets
        transformed_df = self._add_revenue_buckets(transformed_df)

        logger.info(
            "Feature engineering complete. Total Features: %d (Engineered: 8)",
            len(transformed_df.columns),
        )
        return transformed_df

    def _add_total_price(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculates total line-item revenue (TotalPrice = Quantity * UnitPrice)."""
        if "Quantity" in df.columns and "UnitPrice" in df.columns:
            df["TotalPrice"] = (df["Quantity"] * df["UnitPrice"]).round(2)
        else:
            df["TotalPrice"] = 0.0
        return df

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts Year, Month, Quarter, Weekday Name, and Hour from InvoiceDate timestamp."""
        if "InvoiceDate" in df.columns and pd.api.types.is_datetime64_any_dtype(df["InvoiceDate"]):
            dt_col = df["InvoiceDate"].dt
            df["InvoiceYear"] = dt_col.year.astype("int16")
            df["InvoiceMonth"] = dt_col.month.astype("int8")
            df["InvoiceQuarter"] = dt_col.quarter.astype("int8")
            df["InvoiceWeekday"] = dt_col.day_name()
            df["InvoiceHour"] = dt_col.hour.astype("int8")
        else:
            logger.warning("InvoiceDate column missing or not datetime type. Skipping temporal feature extraction.")
        return df

    def _add_cancellation_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        """Flags transaction as cancellation if Quantity < 0 or InvoiceNo begins with 'C'."""
        if "InvoiceNo" in df.columns and "Quantity" in df.columns:
            starts_with_c = df["InvoiceNo"].astype(str).str.startswith("C")
            qty_negative = df["Quantity"] < 0
            df["IsCancellation"] = starts_with_c | qty_negative
        else:
            df["IsCancellation"] = False
        return df

    def _add_customer_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorizes transaction as 'Registered' if CustomerID != 'GUEST' else 'Guest'."""
        if "CustomerID" in df.columns:
            df["CustomerType"] = np.where(df["CustomerID"] == "GUEST", "Guest", "Registered")
        else:
            df["CustomerType"] = "Guest"
        return df

    def _add_revenue_buckets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bins orders into Revenue Buckets: 'Low' (<10), 'Medium' (10-50), 'High' (>50)."""
        if "TotalPrice" in df.columns:
            conditions = [
                df["IsCancellation"],
                df["TotalPrice"] < 10.0,
                (df["TotalPrice"] >= 10.0) & (df["TotalPrice"] <= 50.0),
                df["TotalPrice"] > 50.0,
            ]
            choices = ["Cancellation", "Low (< £10)", "Medium (£10-£50)", "High (> £50)"]
            df["RevenueBucket"] = np.select(conditions, choices, default="Low (< £10)")
        return df
