"""
test_spark_transformer.py
--------------------------
Unit tests for SparkDataTransformer (Phase 7 Milestone 2).
"""

import unittest
from typing import Any

import pandas as pd

from ingestion.spark_transformer import HAS_SPARK, SparkDataTransformer


class TestSparkDataTransformer(unittest.TestCase):

    def setUp(self):
        self.transformer = SparkDataTransformer()
        self.sample_data = pd.DataFrame([
            {
                "InvoiceNo": "536365",
                "StockCode": "85123a",
                "Description": "white heart",
                "Quantity": 6,
                "InvoiceDate": "2010-12-01 08:26:00",
                "UnitPrice": 2.55,
                "CustomerID": "17850",
                "Country": "united kingdom",
            },
            {
                "InvoiceNo": "C536366",
                "StockCode": "71053",
                "Description": None,
                "Quantity": -1,
                "InvoiceDate": "2010-12-01 08:28:00",
                "UnitPrice": 3.00,
                "CustomerID": None,
                "Country": "france",
            },
        ])
        self.sample_data["InvoiceDate"] = pd.to_datetime(self.sample_data["InvoiceDate"])

    def test_transform_fallback_or_spark(self):
        """Verify feature transformation produces expected schema and calculated fields."""
        transformed = self.transformer.transform(self.sample_data)
        self.assertIn("TotalPrice", transformed.columns)
        self.assertIn("IsCancellation", transformed.columns)
        self.assertIn("CustomerType", transformed.columns)
        self.assertIn("RevenueBucket", transformed.columns)
        self.assertIn("InvoiceYear", transformed.columns)

        # Check total price calculation: 6 * 2.55 = 15.30
        self.assertEqual(transformed.iloc[0]["TotalPrice"], 15.30)
        self.assertEqual(transformed.iloc[1]["IsCancellation"], True)


if __name__ == "__main__":
    unittest.main()
