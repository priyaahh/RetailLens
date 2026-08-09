"""
test_validator.py
------------------
Unit test suite for DataValidator class in ingestion/validator.py.
"""

import unittest
from datetime import datetime, timedelta

import pandas as pd

from ingestion.validator import DataValidator, SchemaValidationError


class TestDataValidator(unittest.TestCase):

    def setUp(self):
        self.validator = DataValidator()

    def test_valid_dataset_validation(self):
        """Verify report for a 100% clean valid dataset."""
        data = {
            "InvoiceNo": ["536365", "536366"],
            "StockCode": ["85123A", "71053"],
            "Description": ["WHITE HANGING HEART T-LIGHT HOLDER", "WHITE METAL LANTERN"],
            "Quantity": [6, 6],
            "InvoiceDate": ["2010-12-01 08:26:00", "2010-12-01 08:28:00"],
            "UnitPrice": [2.55, 3.39],
            "CustomerID": ["17850", "17850"],
            "Country": ["United Kingdom", "United Kingdom"],
        }
        df = pd.DataFrame(data)
        report, validated_df = self.validator.validate(df)

        self.assertTrue(report.is_valid)
        self.assertEqual(report.total_rows, 2)
        self.assertEqual(report.invalid_rows, 0)
        self.assertEqual(len(report.error_counts), 0)

    def test_empty_dataset_raises_schema_error(self):
        """Verify SchemaValidationError is raised when dataset is empty."""
        empty_df = pd.DataFrame()
        with self.assertRaises(SchemaValidationError):
            self.validator.validate(empty_df)

    def test_duplicate_column_headers_raises_schema_error(self):
        """Verify SchemaValidationError is raised when headers contain duplicates."""
        data = [["536365", "85123A", "536365"]]
        cols = ["InvoiceNo", "StockCode", "InvoiceNo"]
        df = pd.DataFrame(data, columns=cols)
        with self.assertRaises(SchemaValidationError):
            self.validator.validate(df)

    def test_business_rules_validation_detects_errors(self):
        """Verify business rules flag negative unit price, missing invoice ID, and future dates."""
        future_date_str = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        data = {
            "InvoiceNo": [None, "536366", "536367"],
            "StockCode": ["85123A", "71053", "22423"],
            "Description": ["HOLDER", "LANTERN", "PLATE"],
            "Quantity": [6, -2, 10],  # -2 is return
            "InvoiceDate": ["2010-12-01 08:26:00", "invalid_date_str", future_date_str],
            "UnitPrice": [-2.55, 3.39, 5.00],  # -2.55 is negative price
            "CustomerID": ["17850", "17850", "17851"],
            "Country": ["United Kingdom", "United Kingdom", "France"],
        }
        df = pd.DataFrame(data)
        report, validated_df = self.validator.validate(df)

        self.assertIn("MISSING_INVOICE_NO", report.error_counts)
        self.assertIn("NEGATIVE_UNIT_PRICE", report.error_counts)
        self.assertIn("INVALID_DATE_FORMAT", report.error_counts)
        self.assertIn("FUTURE_INVOICE_DATE", report.error_counts)
        self.assertGreater(report.invalid_rows, 0)


if __name__ == "__main__":
    unittest.main()
