"""
test_kpis.py
------------
Unit tests for KPICalculator class using in-memory SQLite database.
Tests empty database behavior, division-by-zero handling, and KPI accuracy.
"""

import unittest
from sqlalchemy import create_engine, text

from analytics.kpis import KPICalculator


class TestKPICalculator(unittest.TestCase):

    def setUp(self):
        # Create in-memory SQLite database engine
        self.engine = create_engine("sqlite:///:memory:")
        self.kpi_calculator = KPICalculator(engine=self.engine)

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

    def test_empty_database_kpi_handling(self):
        """Verify empty database returns predictable 0.0 metrics without division-by-zero errors."""
        self.assertEqual(self.kpi_calculator.total_revenue(), 0.0)
        self.assertEqual(self.kpi_calculator.total_orders(), 0)
        self.assertEqual(self.kpi_calculator.average_order_value(), 0.0)
        self.assertEqual(self.kpi_calculator.cancellation_rate(), 0.0)
        self.assertEqual(self.kpi_calculator.top_product(), "N/A")

    def test_kpi_calculations_with_data(self):
        """Verify accurate KPI metric calculations with deterministic test data."""
        with self.engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO fact_sales (
                    invoice_no, stock_code, description, quantity, unit_price, total_amount,
                    invoice_timestamp, invoice_year, invoice_month, invoice_quarter, day_of_week,
                    invoice_hour, customer_id, customer_type, country, is_cancellation, revenue_bucket
                ) VALUES 
                ('536365', '85123A', 'WHITE HANGING HEART', 6, 2.55, 15.30, '2010-12-01 08:26:00', 2010, 12, 4, 'Wednesday', 8, '17850', 'Registered', 'United Kingdom', 0, 'Medium (£10-£50)'),
                ('536366', '71053', 'WHITE METAL LANTERN', 10, 3.00, 30.00, '2010-12-01 08:28:00', 2010, 12, 4, 'Wednesday', 8, '17850', 'Registered', 'United Kingdom', 0, 'Medium (£10-£50)'),
                ('C536367', '22423', 'REGENCY CAKESTAND', -1, 12.75, -12.75, '2010-12-02 10:15:00', 2010, 12, 4, 'Thursday', 10, '17851', 'Registered', 'France', 1, 'Cancellation');
            """))

        kpis = self.kpi_calculator.get_all_kpis()

        # Total revenue: 15.30 + 30.00 = 45.30
        self.assertEqual(kpis["total_revenue"], 45.30)
        self.assertEqual(kpis["total_orders"], 2)
        self.assertEqual(kpis["total_units_sold"], 16)
        self.assertEqual(kpis["average_order_value"], 22.65)  # 45.30 / 2
        self.assertEqual(kpis["top_product"], "WHITE METAL LANTERN")  # £30 vs £15.30
        self.assertEqual(kpis["top_country"], "United Kingdom")


if __name__ == "__main__":
    unittest.main()
