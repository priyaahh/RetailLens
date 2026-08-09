"""
test_pipeline.py
----------------
Unit and integration tests for ETLPipeline in ingestion/pipeline.py.
"""

import os
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ingestion.pipeline import ETLPipeline, PipelineConfig


class TestETLPipeline(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config = PipelineConfig(output_dir=self.temp_dir.name)
        self.pipeline = ETLPipeline(config=self.config)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_successful_pipeline_execution(self):
        """Verify end-to-end pipeline execution from CSV to processed staging file."""
        valid_data = {
            "InvoiceNo": ["536365", "536366"],
            "StockCode": ["85123A", "71053"],
            "Description": ["WHITE HANGING HEART", "WHITE METAL LANTERN"],
            "Quantity": [6, 12],
            "InvoiceDate": ["2010-12-01 08:26:00", "2010-12-01 08:28:00"],
            "UnitPrice": [2.55, 3.39],
            "CustomerID": ["17850", "17850"],
            "Country": ["United Kingdom", "United Kingdom"],
        }
        df = pd.DataFrame(valid_data)

        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            raw_path = tmp.name

        try:
            result = self.pipeline.run(raw_path)

            self.assertEqual(result.status, "SUCCESS")
            self.assertEqual(result.total_rows_read, 2)
            self.assertEqual(result.transformed_rows, 2)
            self.assertGreater(result.duration_seconds, 0.0)
            self.assertTrue(os.path.exists(result.output_file_path))

            # Read output staging file and verify engineered features
            processed_df = pd.read_csv(result.output_file_path)
            self.assertIn("TotalPrice", processed_df.columns)
            self.assertIn("InvoiceYear", processed_df.columns)
            self.assertIn("IsCancellation", processed_df.columns)
        finally:
            Path(raw_path).unlink(missing_ok=True)

    def test_pipeline_handles_critical_schema_failure(self):
        """Verify pipeline handles critical schema failure gracefully returning status FAILED."""
        invalid_data = {"InvalidHeader": ["123", "456"]}
        df = pd.DataFrame(invalid_data)

        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            raw_path = tmp.name

        try:
            result = self.pipeline.run(raw_path)
            self.assertEqual(result.status, "FAILED")
            self.assertIn("Missing required columns", result.error_message)
        finally:
            Path(raw_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
