"""
watermark.py
------------
Watermark & File Ingestion Tracker Module for RetailLens.
Provides SHA-256 hash calculation, processed file checking, high-watermark timestamp tracking,
and incremental ETL filtering to guarantee idempotent pipeline executions.
"""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Union

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from database.connection import get_db_engine

logger = logging.getLogger(__name__)


class WatermarkManager:
    """Manages high-watermark timestamps and file processing hashes for incremental ETL."""

    def __init__(self, engine: Optional[Engine] = None):
        """Dependency injection constructor for SQLAlchemy Engine."""
        self.engine = engine or get_db_engine()

    def compute_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Computes SHA-256 hash of a file's content to detect duplicate file re-runs.

        :param file_path: Path to target file.
        :return: Hexadecimal SHA-256 digest string.
        """
        path = Path(file_path)
        hasher = hashlib.sha256()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)

        file_hash = hasher.hexdigest()
        logger.debug("Computed SHA-256 hash for %s: %s", path.name, file_hash[:12])
        return file_hash

    def is_file_processed(self, file_hash: str) -> bool:
        """
        Checks whether a file SHA-256 hash has already been processed in `etl_watermarks`.

        :param file_hash: SHA-256 digest string.
        :return: True if file hash exists in etl_watermarks, False otherwise.
        """
        try:
            query = "SELECT COUNT(*) FROM etl_watermarks WHERE file_hash = :file_hash;"
            with self.engine.connect() as conn:
                count = conn.execute(text(query), {"file_hash": file_hash}).scalar()
                return bool(count and count > 0)
        except Exception as e:
            logger.warning("Unable to check file watermark in database (table may not exist yet): %s", str(e))
            return False

    def get_high_watermark_timestamp(self, table_name: str = "fact_sales") -> Optional[datetime]:
        """
        Retrieves the maximum invoice_timestamp currently loaded in fact_sales.

        :param table_name: Target fact table name.
        :return: Maximum timestamp datetime or None if table is empty.
        """
        try:
            query = f"SELECT MAX(invoice_timestamp) FROM {table_name};"
            with self.engine.connect() as conn:
                max_ts = conn.execute(text(query)).scalar()
                if max_ts is not None:
                    if isinstance(max_ts, str):
                        max_ts = pd.to_datetime(max_ts).to_pydatetime()
                    logger.info("Retrieved high-watermark timestamp for %s: %s", table_name, max_ts)
                    return max_ts
        except Exception as e:
            logger.warning("Could not fetch high-watermark timestamp from database: %s", str(e))
        return None

    def record_watermark(
        self,
        file_path: str,
        file_hash: str,
        high_watermark_ts: Optional[datetime] = None,
        rows_processed: int = 0,
    ) -> bool:
        """
        Records or updates file ingestion metadata in etl_watermarks table.

        :param file_path: Target dataset file path string.
        :param file_hash: SHA-256 hash digest.
        :param high_watermark_ts: Maximum invoice timestamp in ingested file.
        :param rows_processed: Number of rows successfully ingested.
        :return: True on success.
        """
        try:
            query = """
                INSERT INTO etl_watermarks (file_path, file_hash, high_watermark_timestamp, rows_processed)
                VALUES (:file_path, :file_hash, :high_watermark_ts, :rows_processed)
                ON CONFLICT (file_hash) DO UPDATE 
                SET rows_processed = etl_watermarks.rows_processed + EXCLUDED.rows_processed,
                    high_watermark_timestamp = COALESCE(EXCLUDED.high_watermark_timestamp, etl_watermarks.high_watermark_timestamp);
            """
            with self.engine.begin() as conn:
                conn.execute(
                    text(query),
                    {
                        "file_path": str(file_path),
                        "file_hash": file_hash,
                        "high_watermark_ts": high_watermark_ts,
                        "rows_processed": rows_processed,
                    },
                )
            logger.info("Successfully recorded watermark entry for %s (Hash: %s...)", Path(file_path).name, file_hash[:10])
            return True
        except Exception as e:
            logger.warning("Could not record watermark in database: %s", str(e))
            return False

    def filter_incremental_dataframe(
        self, df: pd.DataFrame, watermark_ts: Optional[datetime], timestamp_col: str = "InvoiceDate"
    ) -> Tuple[pd.DataFrame, int]:
        """
        Filters input DataFrame to retain only records with timestamp > watermark_ts.

        :param df: Input DataFrame.
        :param watermark_ts: High-watermark timestamp bound.
        :param timestamp_col: Column containing timestamp records.
        :return: Tuple of (Filtered DataFrame, Skipped Row Count).
        """
        if df.empty or watermark_ts is None or timestamp_col not in df.columns:
            return df, 0

        initial_count = len(df)
        ts_series = pd.to_datetime(df[timestamp_col], errors="coerce")
        filtered_df = df[ts_series > watermark_ts].copy()

        skipped_count = initial_count - len(filtered_df)
        if skipped_count > 0:
            logger.info(
                "Incremental Watermark Filter: Skipped %d historical records (<= %s). Retained %d new records.",
                skipped_count,
                watermark_ts,
                len(filtered_df),
            )

        return filtered_df, skipped_count
