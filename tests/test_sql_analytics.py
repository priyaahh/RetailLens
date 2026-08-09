"""
test_sql_analytics.py
----------------------
Unit and integration tests for SQLAnalyticsService layer using in-memory SQLite database.
"""

import unittest
import pandas as pd
from sqlalchemy import create_engine, text

from analytics.sql_analytics import SQLAnalyticsService


class TestSQLAnalyticsService(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database engine with schema matching fact_sales
        self.engine = create_engine("sqlite:///:memory:")
        self.service = SQLAnalyticsService(engine=self.engine)

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
                    revenue_bucket TEXT NOT NULL
                );
            """))

            # Insert deterministic test data
            conn.execute(text("""
                INSERT INTO fact_sales (
                    invoice_no, stock_code, description, quantity, unit_price, total_amount,
                    invoice_timestamp, invoice_year, invoice_month, invoice_quarter, day_of_week,
                    invoice_hour, customer_id, customer_type, country, is_cancellation, revenue_bucket
                ) VALUES 
                ('536365', '85123A', 'WHITE HANGING HEART', 6, 2.55, 15.30, '2010-12-01 08:26:00', 2010, 12, 4, 'Wednesday', 8, '17850', 'Registered', 'United Kingdom', 0, 'Medium (£10-£50)'),
                ('536366', '71053', 'WHITE METAL LANTERN', 10, 3.00, 30.00, '2010-12-01 08:28:00', 2010, 12, 4, 'Wednesday', 8, 'GUEST', 'Guest', 'France', 0, 'Medium (£10-£50)'),
                ('C536367', '22423', 'REGENCY CAKESTAND', -1, 12.75, -12.75, '2010-12-02 10:15:00', 2010, 12, 4, 'Thursday', 10, '17850', 'Registered', 'United Kingdom', 1, 'Cancellation');
            """))

    def test_customer_summary(self):
        """Verify get_customer_summary returns correct customer breakdown."""
        df = self.service.get_customer_summary()
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 2)  # Guest and Registered
        registered_row = df[df["customer_type"] == "Registered"].iloc[0]
        self.assertEqual(registered_row["total_revenue"], 15.30)

    def test_top_products_by_revenue(self):
        """Verify get_top_products_by_revenue orders products correctly."""
        df = self.service.get_top_products_by_revenue(limit=10)
        self.assertFalse(df.empty)
        self.assertEqual(df.iloc[0]["stock_code"], "71053")  # £30.00 vs £15.30
        self.assertEqual(df.iloc[0]["total_revenue"], 30.00)

    def test_revenue_by_country(self):
        """Verify get_revenue_by_country groups sales by geography."""
        df = self.service.get_revenue_by_country()
        self.assertEqual(len(df), 2)
        france_row = df[df["country"] == "France"].iloc[0]
        self.assertEqual(france_row["total_revenue"], 30.00)


if __name__ == "__main__":
    unittest.main()
