"""
test_cleaner_transformer.py
-----------------------------
Unit tests for DataCleaner and DataTransformer modules in ingestion/.
"""

import unittest
import pandas as pd

from ingestion.cleaner import DataCleaner
from ingestion.transformer import DataTransformer


class TestCleanerAndTransformer(unittest.TestCase):

    def setUp(self):
        self.cleaner = DataCleaner()
        self.transformer = DataTransformer()

    def test_cleaner_imputation_whitespace_and_duplicates(self):
        """Verify cleaner strips whitespace, imputes nulls, and removes duplicate records."""
        data = {
            "InvoiceNo": [" 536365 ", "536365 ", "536366"],
            "StockCode": ["85123a", "85123a", "71053"],
            "Description": [" WHITE HEART ", " WHITE HEART ", None],
            "Quantity": [6, 6, 10],
            "InvoiceDate": ["2010-12-01 08:26:00", "2010-12-01 08:26:00", "2010-12-01 09:15:00"],
            "UnitPrice": [2.55, 2.55, -5.00],  # -5.00 is invalid negative price
            "CustomerID": [None, None, "17850"],
            "Country": [" united kingdom ", " united kingdom ", "france"],
        }
        df = pd.DataFrame(data)
        cleaned_df, stats = self.cleaner.clean(df)

        # Negative price record dropped (3 rows -> 2 rows)
        self.assertEqual(stats["invalid_prices_removed"], 1)

        # Duplicate row dropped (2 rows -> 1 row)
        self.assertEqual(stats["duplicates_removed"], 1)
        self.assertEqual(len(cleaned_df), 1)

        # Verify whitespace & casing normalization
        first_row = cleaned_df.iloc[0]
        self.assertEqual(first_row["InvoiceNo"], "536365")
        self.assertEqual(first_row["StockCode"], "85123A")
        self.assertEqual(first_row["Country"], "United Kingdom")

        # Verify missing CustomerID imputed as GUEST
        self.assertEqual(first_row["CustomerID"], "GUEST")

    def test_transformer_feature_engineering(self):
        """Verify transformer calculates TotalPrice, temporal attributes, flags, and revenue buckets."""
        data = {
            "InvoiceNo": ["536365", "C536366"],
            "StockCode": ["85123A", "71053"],
            "Description": ["WHITE HANGING HEART", "WHITE METAL LANTERN"],
            "Quantity": [10, -2],
            "InvoiceDate": pd.to_datetime(["2010-12-01 08:26:00", "2010-12-05 14:30:00"]),
            "UnitPrice": [3.00, 5.00],
            "CustomerID": ["17850", "GUEST"],
            "Country": ["United Kingdom", "United Kingdom"],
        }
        cleaned_df = pd.DataFrame(data)
        transformed_df = self.transformer.transform(cleaned_df)

        # TotalPrice checks
        self.assertEqual(transformed_df.iloc[0]["TotalPrice"], 30.00)
        self.assertEqual(transformed_df.iloc[1]["TotalPrice"], -10.00)

        # Temporal feature checks
        self.assertEqual(transformed_df.iloc[0]["InvoiceYear"], 2010)
        self.assertEqual(transformed_df.iloc[0]["InvoiceMonth"], 12)
        self.assertEqual(transformed_df.iloc[0]["InvoiceQuarter"], 4)
        self.assertEqual(transformed_df.iloc[0]["InvoiceWeekday"], "Wednesday")
        self.assertEqual(transformed_df.iloc[0]["InvoiceHour"], 8)

        # Cancellation flag checks
        self.assertFalse(transformed_df.iloc[0]["IsCancellation"])
        self.assertTrue(transformed_df.iloc[1]["IsCancellation"])

        # CustomerType checks
        self.assertEqual(transformed_df.iloc[0]["CustomerType"], "Registered")
        self.assertEqual(transformed_df.iloc[1]["CustomerType"], "Guest")

        # RevenueBucket checks
        self.assertEqual(transformed_df.iloc[0]["RevenueBucket"], "Medium (£10-£50)")
        self.assertEqual(transformed_df.iloc[1]["RevenueBucket"], "Cancellation")

    def test_cleaner_numeric_string_columns(self):
        """Verify cleaner handles numerical StockCode and InvoiceNo without AttributeError."""
        data = {
            "InvoiceNo": [536365, 536366],
            "StockCode": [85123, 71053],
            "Description": ["WHITE HEART", "LANTERN"],
            "Quantity": [6, 10],
            "InvoiceDate": ["2010-12-01 08:26:00", "2010-12-01 09:15:00"],
            "UnitPrice": [2.55, 3.00],
            "CustomerID": [17850, None],
            "Country": ["United Kingdom", "France"],
        }
        df = pd.DataFrame(data)
        cleaned_df, _ = self.cleaner.clean(df)
        self.assertEqual(cleaned_df.iloc[0]["InvoiceNo"], "536365")
        self.assertEqual(cleaned_df.iloc[0]["StockCode"], "85123")


if __name__ == "__main__":
    unittest.main()
