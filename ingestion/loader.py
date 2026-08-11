"""
loader.py
---------
Production-grade Database Loading & Persistence engine for RetailLens.
Manages bulk batch insertion into PostgreSQL using SQLAlchemy transaction contexts,
atomic commit/rollback handling, column name mapping, connection pooling, and idempotent deduplication.
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


@dataclass
class LoadResult:
    """Encapsulates database loading metrics, status, and transaction details."""
    status: str = "PENDING"  # SUCCESS, FAILED
    table_name: str = ""
    rows_inserted: int = 0
    rows_skipped_duplicate: int = 0
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
        idempotent: bool = True,
    ) -> LoadResult:
        """
        Executes atomic batch loading of DataFrame into specified database table.

        :param df: Transformed Pandas DataFrame.
        :param table_name: Target database table name.
        :param if_exists: How to handle existing table ('append', 'replace', 'fail').
        :param chunksize: Number of rows to insert per bulk SQL batch.
        :param idempotent: If True, filters out duplicate natural keys already present in table.
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

            # 2. Idempotent Deduplication against existing table
            if idempotent and if_exists == "append":
                db_df, result.rows_skipped_duplicate = self._deduplicate_against_database(db_df, table_name)

            if db_df.empty:
                logger.info("All records in batch already exist in '%s'. Skipped %d duplicate records.", table_name, result.rows_skipped_duplicate)
                result.status = "SUCCESS"
                result.rows_inserted = 0
                result.duration_seconds = round(time.time() - start_ts, 3)
                return result

            # 3. Execute Atomic Transaction
            with self.engine.begin() as conn:
                db_df.to_sql(
                    name=table_name,
                    con=conn,
                    if_exists=if_exists,
                    index=False,
                    chunksize=chunksize,
                    method="multi",  # Combines multiple rows into a single multi-row SQL INSERT statement
                )

            result.status = "SUCCESS"
            result.rows_inserted = len(db_df)
            result.duration_seconds = round(time.time() - start_ts, 3)
            logger.info(
                "Successfully persisted %d rows into '%s' in %.3f seconds (Skipped duplicates: %d).",
                result.rows_inserted,
                table_name,
                result.duration_seconds,
                result.rows_skipped_duplicate,
            )
            return result

        except Exception as e:
            logger.error("Failed to load DataFrame into table '%s': %s", table_name, str(e), exc_info=True)
            result.status = "FAILED"
            result.error_message = str(e)
            result.duration_seconds = round(time.time() - start_ts, 3)
            return result

    def _map_columns_to_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """Renames DataFrame columns to match database schema conventions."""
        mapped_df = df.copy()
        mapped_columns = {col: self.COLUMN_MAPPING[col] for col in df.columns if col in self.COLUMN_MAPPING}
        mapped_df = mapped_df.rename(columns=mapped_columns)
        return mapped_df

    def _deduplicate_against_database(self, db_df: pd.DataFrame, table_name: str) -> Tuple[pd.DataFrame, int]:
        """Filters out records whose composite natural keys exist in table_name."""
        key_cols = ["invoice_no", "stock_code", "invoice_timestamp"]
        if not all(col in db_df.columns for col in key_cols):
            return db_df, 0

        try:
            query = f"SELECT invoice_no, stock_code, invoice_timestamp FROM {table_name};"
            with self.engine.connect() as conn:
                existing_df = pd.read_sql_query(query, conn)

            if existing_df.empty:
                return db_df, 0

            # Convert timestamp to string/datetime format matching existing_df
            existing_df["invoice_timestamp"] = pd.to_datetime(existing_df["invoice_timestamp"])
            db_df["invoice_timestamp"] = pd.to_datetime(db_df["invoice_timestamp"])

            # Left anti-join to isolate unique non-existing records
            merged = db_df.merge(
                existing_df[key_cols].drop_duplicates(),
                on=key_cols,
                how="left",
                indicator=True,
            )
            unique_df = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])

            skipped_count = len(db_df) - len(unique_df)
            return unique_df, skipped_count

        except Exception as e:
            logger.debug("Could not deduplicate against existing table (may be new table): %s", str(e))
            return db_df, 0
