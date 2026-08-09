"""
test_loader.py
--------------
Unit tests for DatabaseLoader module using SQLite memory database.
"""

import unittest
import pandas as pd
from sqlalchemy import create_engine, text

from ingestion.loader import DatabaseLoader


class TestDatabaseLoader(unittest.TestCase):

    def setUp(self):
        # Create an in-memory SQLite database engine for fast, isolated testing
        self.engine = create_engine("sqlite:///:memory:")
        self.loader = DatabaseLoader(engine=self.engine)

    def test_database_loader_successful_insert(self):
        """Verify successful bulk insertion and column mapping into database."""
        data = {
            "InvoiceNo": ["536365"],
            "StockCode": ["85123A"],
            "Description": ["WHITE HANGING HEART"],
            "Quantity": [6],
            "UnitPrice": [2.55],
            "TotalPrice": [15.30],
            "InvoiceDate": pd.to_datetime(["2010-12-01 08:26:00"]),
            "InvoiceYear": [2010],
            "InvoiceMonth": [12],
            "InvoiceQuarter": [4],
            "InvoiceWeekday": ["Wednesday"],
            "InvoiceHour": [8],
            "CustomerID": ["17850"],
            "CustomerType": ["Registered"],
            "Country": ["United Kingdom"],
            "IsCancellation": [False],
            "RevenueBucket": ["Medium (£10-£50)"],
        }
        df = pd.DataFrame(data)

        # Perform load
        result = self.loader.load(df, table_name="test_fact_sales", if_exists="replace")

        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.rows_inserted, 1)

        # Verify inserted row content in SQLite
        with self.engine.connect() as conn:
            query = text("SELECT invoice_no, total_amount, customer_type FROM test_fact_sales")
            row = conn.execute(query).fetchone()
            self.assertEqual(row[0], "536365")
            self.assertEqual(row[1], 15.30)
            self.assertEqual(row[2], "Registered")

    def test_empty_dataframe_load(self):
        """Verify empty DataFrame returns success with 0 inserted rows."""
        empty_df = pd.DataFrame()
        result = self.loader.load(empty_df, table_name="test_fact_sales")
        self.assertEqual(result.status, "SUCCESS")
        self.assertEqual(result.rows_inserted, 0)


if __name__ == "__main__":
    unittest.main()
