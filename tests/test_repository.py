"""
test_repository.py
------------------
Unit tests for AnalyticsRepository data access layer using mock engine and in-memory SQLite.
"""

import unittest
from unittest.mock import MagicMock
from sqlalchemy import create_engine, text

from analytics.exceptions import InvalidFilterError, RepositoryError
from analytics.models import FilterParams
from analytics.repository import AnalyticsRepository


class TestAnalyticsRepository(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database
        self.engine = create_engine("sqlite:///:memory:")
        self.repo = AnalyticsRepository(engine=self.engine)

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

    def test_filter_where_clause_building(self):
        """Verify dynamic SQL WHERE clause construction."""
        filters = FilterParams(
            start_date="2010-12-01",
            end_date="2010-12-31",
            country="France",
            customer_type="Registered",
            transaction_type="Sales",
        )
        where_sql, params = self.repo._build_where_clause(filters)
        self.assertIn("invoice_timestamp >=", where_sql)
        self.assertIn("country = :country", where_sql)
        self.assertEqual(params["country"], "France")

    def test_invalid_filter_date_range(self):
        """Verify invalid date range raises InvalidFilterError."""
        filters = FilterParams(start_date="2020-12-31", end_date="2010-01-01")
        with self.assertRaises(InvalidFilterError):
            self.repo._build_where_clause(filters)

    def test_empty_repository_metrics(self):
        """Verify empty database returns zero scalar values cleanly."""
        self.assertEqual(self.repo.get_total_revenue(), 0.0)
        self.assertEqual(self.repo.get_total_orders(), 0)
        self.assertEqual(self.repo.get_average_order_value(), 0.0)
        self.assertEqual(self.repo.get_cancellation_rate(), 0.0)

    def test_repository_with_data(self):
        """Verify query output accuracy with deterministic SQLite test records."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO fact_sales (
                    invoice_no, stock_code, description, quantity, unit_price, total_amount,
                    invoice_timestamp, invoice_year, invoice_month, invoice_quarter, day_of_week,
                    invoice_hour, customer_id, customer_type, country, is_cancellation, revenue_bucket
                ) VALUES 
                ('536365', '85123A', 'WHITE HEART', 6, 2.50, 15.00, '2010-12-01 08:26:00', 2010, 12, 4, 'Wednesday', 8, '17850', 'Registered', 'United Kingdom', 0, 'Medium'),
                ('536366', '71053', 'WHITE LANTERN', 10, 3.00, 30.00, '2010-12-01 08:28:00', 2010, 12, 4, 'Wednesday', 8, 'GUEST', 'Guest', 'France', 0, 'Medium');
            """))

        self.assertEqual(self.repo.get_total_revenue(), 45.00)
        self.assertEqual(self.repo.get_total_orders(), 2)
        self.assertEqual(self.repo.get_average_order_value(), 22.50)


if __name__ == "__main__":
    unittest.main()
