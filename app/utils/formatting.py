"""
formatting.py
-------------
Utility module providing standardized formatting helper functions for
currency (£), numbers, percentages, and dates across the RetailLens dashboard.
"""

from datetime import date, datetime
from typing import Optional, Union


def format_currency(value: Optional[Union[int, float]]) -> str:
    """
    Formats a numeric value as British Pound Sterling (£) currency with human-readable scaling.

    :param value: Numeric value to format.
    :return: Formatted currency string (e.g. £1.25M, £45.30K, £100.42).
    """
    if value is None:
        return "£0.00"

    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000:
        return f"{sign}£{abs_val / 1_000_000:.2f}M"
    elif abs_val >= 100_000:
        return f"{sign}£{abs_val / 1_000:.1f}K"
    elif abs_val >= 1_000:
        return f"{sign}£{abs_val:,.2f}"
    else:
        return f"{sign}£{abs_val:.2f}"


def format_number(value: Optional[Union[int, float]]) -> str:
    """
    Formats integers or large numbers with thousands separators and scaling.

    :param value: Numeric value to format.
    :return: Formatted number string (e.g. 145,320 or 1.2M).
    """
    if value is None:
        return "0"

    abs_val = abs(value)
    sign = "-" if value < 0 else ""

    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.2f}M"
    else:
        return f"{sign}{value:,.0f}" if isinstance(value, int) or value.is_integer() else f"{sign}{value:,.2f}"


def format_percentage(value: Optional[Union[int, float]], decimals: int = 1) -> str:
    """
    Formats a decimal or float value as a percentage string.

    :param value: Float value (e.g. 4.7 for 4.7%).
    :param decimals: Number of decimal places.
    :return: Formatted percentage string (e.g. 4.7%).
    """
    if value is None:
        return "0.0%"
    return f"{value:.{decimals}f}%"


def format_date(value: Optional[Union[str, date, datetime]], fmt: str = "%b %d, %Y") -> str:
    """
    Formats a datetime or date string into a clean human-readable date.

    :param value: Date string or object.
    :param fmt: Target strftime pattern.
    :return: Formatted date string.
    """
    if value is None:
        return "N/A"

    if isinstance(value, (datetime, date)):
        return value.strftime(fmt)

    try:
        dt = datetime.strptime(str(value)[:10], "%Y-%m-%d")
        return dt.strftime(fmt)
    except Exception:
        return str(value)
