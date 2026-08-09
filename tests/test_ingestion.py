"""
test_ingestion.py
-----------------
Unit tests for the DataFileReader module using pytest and unittest.
"""

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from config.schema_config import IngestionConfig
from ingestion.reader import DataFileReader


class TestDataFileReader(unittest.TestCase):

    def setUp(self):
        self.config = IngestionConfig()
        self.reader = DataFileReader(config=self.config)

    def test_file_not_found(self):
        """Verify FileNotFoundError is raised when file does not exist."""
        non_existent_path = "data/raw/does_not_exist.csv"
        with self.assertRaises(FileNotFoundError):
            self.reader.read_file(non_existent_path)

    def test_unsupported_extension(self):
        """Verify ValueError is raised when file extension is invalid."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"sample text content")
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                self.reader.read_file(tmp_path)
            self.assertIn("Unsupported file format", str(ctx.exception))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_missing_required_columns(self):
        """Verify ValueError is raised when required header columns are missing."""
        invalid_data = {
            "InvoiceNo": ["536365"],
            "Description": ["WHITE HANGING HEART T-LIGHT HOLDER"],
            # Missing StockCode, Quantity, InvoiceDate, UnitPrice
        }
        df = pd.DataFrame(invalid_data)

        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name

        try:
            with self.assertRaises(ValueError) as ctx:
                self.reader.read_file(tmp_path)
            self.assertIn("Missing required columns", str(ctx.exception))
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_valid_csv_ingestion(self):
        """Verify successful ingestion of a valid CSV dataset."""
        valid_data = {
            "InvoiceNo": ["536365", "536366"],
            "StockCode": ["85123A", "71053"],
            "Description": ["WHITE HANGING HEART T-LIGHT HOLDER", "WHITE METAL LANTERN"],
            "Quantity": [6, 6],
            "InvoiceDate": ["2010-12-01 08:26:00", "2010-12-01 08:28:00"],
            "UnitPrice": [2.55, 3.39],
            "CustomerID": ["17850", "17850"],
            "Country": ["United Kingdom", "United Kingdom"],
        }
        df = pd.DataFrame(valid_data)

        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w", delete=False) as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name

        try:
            result_df = self.reader.read_file(tmp_path)
            self.assertEqual(len(result_df), 2)
            self.assertIn("InvoiceNo", result_df.columns)
            self.assertIn("StockCode", result_df.columns)
        finally:
            Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
