"""
loader.py
---------
Production-grade Database Loading & Persistence engine for RetailLens.
Manages bulk batch insertion into PostgreSQL using SQLAlchemy transaction contexts,
atomic commit/rollback handling, column name mapping, and connection pooling.
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Encapsulates database loading metrics, status, and transaction details."""
    status: str = "PENDING"  # SUCCESS, FAILED
    table_name: str = ""
    rows_inserted: int = 0
    duration_seconds: float = 0.0
    error_message: Optional[str] = None


class DatabaseLoader:
    """Database Persistence Loader executing atomic bulk inserts into PostgreSQL."""

    # Column Mapping from DataFrame feature names to Database Schema column names
    COLUMN_MAPPING: Dict[str, str] = {
        "InvoiceNo": "invoice_no",
        "StockCode": "stock_code",
        "Description": "description",
        "Quantity": "quantity",
        "UnitPrice": "unit_price",
        "TotalPrice": "total_amount",
        "InvoiceDate": "invoice_timestamp",
        "InvoiceYear": "invoice_year",
        "InvoiceMonth": "invoice_month",
        "InvoiceQuarter": "invoice_quarter",
        "InvoiceWeekday": "day_of_week",
        "InvoiceHour": "invoice_hour",
        "CustomerID": "customer_id",
        "CustomerType": "customer_type",
        "Country": "country",
        "IsCancellation": "is_cancellation",
        "RevenueBucket": "revenue_bucket",
    }

    def __init__(self, engine: Optional[Engine] = None):
        """Initializes loader with SQLAlchemy Engine dependency injection."""
        self.engine = engine or get_db_engine()

    def load(
        self,
        df: pd.DataFrame,
        table_name: str = "fact_sales",
        if_exists: str = "append",
        chunksize: int = 1000,
    ) -> LoadResult:
        """
        Executes atomic batch loading of DataFrame into specified database table.

        :param df: Transformed Pandas DataFrame.
        :param table_name: Target database table name.
        :param if_exists: How to handle existing table ('append', 'replace', 'fail').
        :param chunksize: Number of rows to insert per bulk SQL batch.
        :return: LoadResult object containing status and row metrics.
        """
        start_ts = time.time()
        result = LoadResult(table_name=table_name)

        if df.empty:
            logger.warning("Empty DataFrame passed to DatabaseLoader. Skipping DB insertion.")
            result.status = "SUCCESS"
            result.rows_inserted = 0
            return result

        logger.info("Starting database bulk load into table '%s' (Rows: %d, Chunksize: %d)...", table_name, len(df), chunksize)

        try:
            # 1. Map DataFrame columns to target DB schema names
            db_df = self._map_columns_to_schema(df)

            # 2. Execute Atomic Transaction
            with self.engine.begin() as conn:
                db_df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists=if_exists,
                    index=False,
                    chunksize=chunksize,
                    method="multi",  # Combines multiple rows into a single multi-row SQL INSERT statement
                )

            end_ts = time.time()
            result.status = "SUCCESS"
            result.rows_inserted = len(db_df)
            result.duration_seconds = round(end_ts - start_ts, 4)

            logger.info(
                "Database load successful! Target: '%s' | Rows Inserted: %d | Time: %.4fs",
                table_name,
                result.rows_inserted,
                result.duration_seconds,
            )

        except Exception as e:
            end_ts = time.time()
            result.status = "FAILED"
            result.duration_seconds = round(end_ts - start_ts, 4)
            result.error_message = f"Database load transaction failed and was rolled back: {str(e)}"
            logger.error(result.error_message, exc_info=True)

        return result

    def _map_columns_to_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renames DataFrame columns to match PostgreSQL target table DDL schema."""
        mapped_df = df.copy()

        # Rename matching columns
        rename_dict = {col: self.COLUMN_MAPPING[col] for col in mapped_df.columns if col in self.COLUMN_MAPPING}
        mapped_df = mapped_df.rename(columns=rename_dict)

        # Drop any leftover columns not in destination schema mapping
        valid_cols = list(self.COLUMN_MAPPING.values())
        mapped_df = mapped_df[[col for col in mapped_df.columns if col in valid_cols]]

        return mapped_df
