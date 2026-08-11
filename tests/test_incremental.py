"""
test_incremental.py
-------------------
Unit and integration tests for WatermarkManager, incremental ETL filtering, and idempotent database loading.
"""

import unittest
from datetime import datetime
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text

from ingestion.loader import DatabaseLoader
from ingestion.watermark import WatermarkManager


class TestIncrementalETL(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.watermark_mgr = WatermarkManager(engine=self.engine)
        self.loader = DatabaseLoader(engine=self.engine)

        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE fact_sales (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT NOT NULL,
                    stock_code TEXT NOT NULL,
                    description TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    invoice_timestamp TIMESTAMP NOT NULL,
                    invoice_year INTEGER NOT NULL,
                    invoice_month INTEGER NOT NULL,
                    invoice_quarter INTEGER NOT NULL,
                    day_of_week TEXT NOT NULL,
                    invoice_hour INTEGER NOT NULL,
                    customer_id TEXT NOT NULL,
                    customer_type TEXT NOT NULL,
                    country TEXT NOT NULL,
                    is_cancellation INTEGER NOT NULL DEFAULT 0,
                    revenue_bucket TEXT NOT NULL,
                    CONSTRAINT uq_fact_sales UNIQUE (invoice_no, stock_code, invoice_timestamp)
                );
            """))

            conn.execute(text("""
                CREATE TABLE etl_watermarks (
                    watermark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL UNIQUE,
                    high_watermark_timestamp TIMESTAMP,
                    rows_processed INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))

    def test_file_hash_computation(self):
        """Verify SHA-256 hash calculation for a test file."""
        test_file = Path("data/raw/test_hash_sample.csv")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("InvoiceNo,StockCode\n536365,85123A\n")

        try:
            h1 = self.watermark_mgr.compute_file_hash(test_file)
            h2 = self.watermark_mgr.compute_file_hash(test_file)
            self.assertEqual(h1, h2)
            self.assertEqual(len(h1), 64)
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_watermark_record_and_check(self):
        """Verify recording and checking watermark hashes in etl_watermarks table."""
        file_hash = "abc123def4567890abc123def4567890abc123def4567890abc123def4567890"
        self.assertFalse(self.watermark_mgr.is_file_processed(file_hash))

        recorded = self.watermark_mgr.record_watermark(
            file_path="data/raw/test.csv",
            file_hash=file_hash,
            high_watermark_ts=datetime(2010, 12, 1, 8, 26),
            rows_processed=100,
        )
        self.assertTrue(recorded)
        self.assertTrue(self.watermark_mgr.is_file_processed(file_hash))

    def test_incremental_dataframe_filtering(self):
        """Verify filtering out records older than high-watermark timestamp."""
        df = pd.DataFrame([
            {"InvoiceNo": "536365", "InvoiceDate": "2010-12-01 08:00:00"},
            {"InvoiceNo": "536366", "InvoiceDate": "2010-12-01 10:00:00"},
            {"InvoiceNo": "536367", "InvoiceDate": "2010-12-01 12:00:00"},
        ])

        watermark_ts = datetime(2010, 12, 1, 9, 0, 0)
        filtered_df, skipped = self.watermark_mgr.filter_incremental_dataframe(df, watermark_ts)

        self.assertEqual(skipped, 1)  # 08:00:00 skipped
        self.assertEqual(len(filtered_df), 2)  # 10:00:00 and 12:00:00 retained

    def test_idempotent_database_loading(self):
        """Verify database loader skips duplicate natural keys when loaded twice."""
        df = pd.DataFrame([
            {
                "InvoiceNo": "536365",
                "StockCode": "85123A",
                "Description": "WHITE HEART",
                "Quantity": 6,
                "UnitPrice": 2.50,
                "TotalPrice": 15.00,
                "InvoiceDate": "2010-12-01 08:26:00",
                "InvoiceYear": 2010,
                "InvoiceMonth": 12,
                "InvoiceQuarter": 4,
                "InvoiceWeekday": "Wednesday",
                "InvoiceHour": 8,
                "CustomerID": "17850",
                "CustomerType": "Registered",
                "Country": "United Kingdom",
                "IsCancellation": False,
                "RevenueBucket": "Medium",
            }
        ])

        # First Load
        res1 = self.loader.load(df, table_name="fact_sales", if_exists="append", idempotent=True)
        self.assertEqual(res1.rows_inserted, 1)
        self.assertEqual(res1.rows_skipped_duplicate, 0)

        # Second Load (Same data - Idempotent re-run)
        res2 = self.loader.load(df, table_name="fact_sales", if_exists="append", idempotent=True)
        self.assertEqual(res2.rows_inserted, 0)
        self.assertEqual(res2.rows_skipped_duplicate, 1)


if __name__ == "__main__":
    unittest.main()
