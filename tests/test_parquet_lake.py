"""
test_parquet_lake.py
--------------------
Unit tests for ParquetDataLake (Phase 7 Milestone 4).
"""

import os
import shutil
import tempfile
import unittest
import pandas as pd

from storage.parquet_lake import ParquetDataLake


class TestParquetDataLake(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.lake = ParquetDataLake(base_lake_dir=self.temp_dir)
        self.sample_df = pd.DataFrame([
            {"InvoiceNo": "536365", "InvoiceYear": 2010, "InvoiceMonth": 12, "TotalPrice": 15.30},
            {"InvoiceNo": "536366", "InvoiceYear": 2010, "InvoiceMonth": 12, "TotalPrice": 30.00},
        ])

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_and_read_lake(self):
        """Verify writing and reading Parquet data lake files."""
        out_path = self.lake.write_to_lake(self.sample_df, zone="processed", partition_cols=["InvoiceYear", "InvoiceMonth"])
        self.assertTrue(len(out_path) > 0)

        df_read = self.lake.read_from_lake(zone="processed")
        self.assertEqual(len(df_read), 2)
        self.assertIn("InvoiceNo", df_read.columns)

        summary = self.lake.get_lake_summary()
        self.assertIn("processed", summary)


if __name__ == "__main__":
    unittest.main()
