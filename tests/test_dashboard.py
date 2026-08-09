"""
test_dashboard.py
-----------------
Unit tests for dashboard formatting utilities and UI helper components.
"""

import unittest
from datetime import date, datetime

from app.utils.formatting import (
    format_currency,
    format_date,
    format_number,
    format_percentage,
)


class TestDashboardFormatting(unittest.TestCase):

    def test_format_currency(self):
        """Verify currency formatting across numeric ranges and nulls."""
        self.assertEqual(format_currency(None), "£0.00")
        self.assertEqual(format_currency(0), "£0.00")
        self.assertEqual(format_currency(45.30), "£45.30")
        self.assertEqual(format_currency(1250.50), "£1,250.50")
        self.assertEqual(format_currency(150000), "£150.0K")
        self.assertEqual(format_currency(1250000), "£1.25M")

    def test_format_number(self):
        """Verify number formatting with comma separators and scaling."""
        self.assertEqual(format_number(None), "0")
        self.assertEqual(format_number(12450), "12,450")
        self.assertEqual(format_number(1250000), "1.25M")

    def test_format_percentage(self):
        """Verify percentage formatting."""
        self.assertEqual(format_percentage(None), "0.0%")
        self.assertEqual(format_percentage(4.7), "4.7%")
        self.assertEqual(format_percentage(12.345, decimals=2), "12.35%")

    def test_format_date(self):
        """Verify date string parsing and formatting."""
        self.assertEqual(format_date(None), "N/A")
        self.assertEqual(format_date("2010-12-01"), "Dec 01, 2010")
        d = date(2026, 8, 9)
        self.assertEqual(format_date(d), "Aug 09, 2026")


if __name__ == "__main__":
    unittest.main()
