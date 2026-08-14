"""
parquet_lake.py
---------------
Parquet Data Lake Storage Layer for RetailLens (Phase 7 Milestone 4).
Implements raw, staged, and processed data lake storage zones with Snappy compression,
columnar schema preservation, and temporal partitioning (year/month).
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ParquetDataLake:
    """Manages Parquet data lake storage zones and temporal directory partitioning."""

    def __init__(self, base_lake_dir: str = "data/lake"):
        """
        Constructor setting up data lake zones.

        :param base_lake_dir: Base directory path for local data lake.
        """
        self.base_lake_dir = Path(base_lake_dir)
        self.raw_zone = self.base_lake_dir / "raw"
        self.staged_zone = self.base_lake_dir / "staged"
        self.processed_zone = self.base_lake_dir / "processed"

        # Create Data Lake Directory Structure
        for zone_path in [self.raw_zone, self.staged_zone, self.processed_zone]:
            os.makedirs(zone_path, exist_ok=True)

    def write_to_lake(
        self,
        df: pd.DataFrame,
        zone: str = "processed",
        partition_cols: Optional[List[str]] = None,
        compression: str = "snappy",
    ) -> str:
        """
        Writes Pandas DataFrame to Parquet format in the specified data lake zone.

        :param df: Input DataFrame.
        :param zone: Lake zone name ('raw', 'staged', 'processed').
        :param partition_cols: Column names to partition directory by (e.g. ['InvoiceYear', 'InvoiceMonth']).
        :param compression: Compression codec ('snappy', 'gzip', None).
        :return: Destination output path string.
        """
        if df.empty:
            logger.warning("Empty DataFrame passed to write_to_lake. Skipping output.")
            return ""

        target_dir = self.base_lake_dir / zone.lower()
        os.makedirs(target_dir, exist_ok=True)

        if partition_cols and all(col in df.columns for col in partition_cols):
            logger.info("Writing DataFrame to Parquet lake zone '%s' with partitioning: %s", zone, partition_cols)
            df.to_parquet(
                path=target_dir,
                engine="pyarrow",
                compression=compression,
                partition_cols=partition_cols,
                index=False,
            )
            output_path = str(target_dir)
        else:
            file_path = target_dir / f"dataset_{zone}.parquet"
            logger.info("Writing DataFrame to single Parquet file: %s", file_path)
            df.to_parquet(
                path=file_path,
                engine="pyarrow",
                compression=compression,
                index=False,
            )
            output_path = str(file_path)

        return output_path

    def read_from_lake(
        self,
        zone: str = "processed",
        columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Reads Parquet dataset from the specified data lake zone.

        :param zone: Target data lake zone ('raw', 'staged', 'processed').
        :param columns: Optional list of columns to project (column pruning).
        :return: Loaded Pandas DataFrame.
        """
        target_dir = self.base_lake_dir / zone.lower()
        if not target_dir.exists():
            logger.warning("Data lake zone '%s' does not exist.", zone)
            return pd.DataFrame()

        try:
            df = pd.read_parquet(target_dir, engine="pyarrow", columns=columns)
            logger.info("Read %d records from Parquet data lake zone '%s'.", len(df), zone)
            return df
        except Exception as e:
            logger.warning("Could not read Parquet dataset from zone '%s': %s", zone, str(e))
            return pd.DataFrame()

    def get_lake_summary(self) -> Dict[str, Any]:
        """Returns statistics on file counts and size across data lake zones."""
        summary = {}
        for zone in ["raw", "staged", "processed"]:
            zone_path = self.base_lake_dir / zone
            files = list(zone_path.glob("**/*.parquet")) + list(zone_path.glob("**/*.csv"))
            total_bytes = sum(f.stat().st_size for f in files)
            summary[zone] = {
                "file_count": len(files),
                "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            }
        return summary
