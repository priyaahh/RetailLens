"""
exceptions.py
-------------
Custom exception hierarchy for the RetailLens Analytics & Repository Layer.
"""


class AnalyticsError(Exception):
    """Base exception class for all analytics module errors."""
    pass


class RepositoryError(AnalyticsError):
    """Raised when an error occurs during database data access or query execution."""
    pass


class DatabaseConnectionError(RepositoryError):
    """Raised when database connection initialization fails."""
    pass


class InvalidFilterError(AnalyticsError):
    """Raised when user-supplied filter parameters (e.g. invalid date ranges) are malformed."""
    pass
