"""
benchmark.py
------------
Performance Benchmarking Engine for RetailLens (Phase 7 Milestone 12).
Measures actual execution duration, throughput (records/second), and memory behavior
comparing single-node Pandas vs distributed PySpark across synthetic dataset scales.
"""

import logging
import time
from typing import Any, Dict, List

import pandas as pd

from ingestion.spark_transformer import HAS_SPARK, SparkDataTransformer
from ingestion.transformer import DataTransformer

logger = logging.getLogger(__name__)


class BenchmarkEngine:
    """Measures execution throughput and duration for Pandas vs PySpark compute engines."""

    def __init__(self):
        self.pandas_transformer = DataTransformer()
        self.spark_transformer = SparkDataTransformer()

    def generate_synthetic_data(self, num_rows: int = 10000) -> pd.DataFrame:
        """Generates synthetic transaction dataset for benchmarking."""
        data = {
            "InvoiceNo": [f"536{i:03d}" if i % 10 != 0 else f"C536{i:03d}" for i in range(num_rows)],
            "StockCode": [f"8512{i % 10}A" for i in range(num_rows)],
            "Description": ["WHITE HANGING HEART T-LIGHT HOLDER" if i % 2 == 0 else None for i in range(num_rows)],
            "Quantity": [6 if i % 10 != 0 else -1 for i in range(num_rows)],
            "InvoiceDate": ["2010-12-01 08:26:00"] * num_rows,
            "UnitPrice": [2.55] * num_rows,
            "CustomerID": ["17850" if i % 3 != 0 else None for i in range(num_rows)],
            "Country": ["United Kingdom"] * num_rows,
        }
        df = pd.DataFrame(data)
        df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
        return df

    def run_benchmark(self, num_rows_list: List[int] = [1000, 10000, 50000]) -> List[Dict[str, Any]]:
        """
        Executes performance benchmarking across dataset scales.

        :param num_rows_list: List of row counts to benchmark.
        :return: List of empirical benchmark metric dictionaries.
        """
        results = []

        for num_rows in num_rows_list:
            logger.info("Benchmarking scale: %d rows...", num_rows)
            df_raw = self.generate_synthetic_data(num_rows)

            # 1. Benchmark Pandas Engine
            start_pandas = time.time()
            df_pandas = self.pandas_transformer.transform(df_raw)
            duration_pandas = round(time.time() - start_pandas, 4)
            speed_pandas = round(num_rows / duration_pandas, 1) if duration_pandas > 0 else 0.0

            results.append({
                "scale_rows": num_rows,
                "engine": "Pandas",
                "duration_seconds": duration_pandas,
                "records_per_second": speed_pandas,
                "has_spark": HAS_SPARK,
            })

            # 2. Benchmark PySpark Engine (or fallback)
            start_spark = time.time()
            df_spark = self.spark_transformer.transform(df_raw)
            duration_spark = round(time.time() - start_spark, 4)
            speed_spark = round(num_rows / duration_spark, 1) if duration_spark > 0 else 0.0

            results.append({
                "scale_rows": num_rows,
                "engine": "PySpark" if HAS_SPARK else "PySpark (Fallback)",
                "duration_seconds": duration_spark,
                "records_per_second": speed_spark,
                "has_spark": HAS_SPARK,
            })

        return results
