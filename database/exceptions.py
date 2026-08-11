"""
exceptions.py (Database & Reliability)
-------------------------------------
Core Exception Hierarchy for RetailLens database, ETL pipeline, and reliability layers.
Differentiates between retryable transient errors and non-retryable permanent errors.
"""


class RetailLensError(Exception):
    """Base exception class for all RetailLens application errors."""
    pass


class DatabaseError(RetailLensError):
    """Base exception for database persistence failures."""
    pass


class TransientDatabaseError(DatabaseError):
    """
    Retryable database exception.
    Raised on transient network glitches, connection timeouts, or temporary deadlocks.
    """
    pass


class PermanentDatabaseError(DatabaseError):
    """
    Non-retryable database exception.
    Raised on DDL syntax errors, foreign key constraint violations, or column mismatch errors.
    """
    pass


class PipelineError(RetailLensError):
    """Base exception for ETL pipeline execution failures."""
    pass
