"""
test_reliability.py
-------------------
Unit tests for database retry mechanisms, transient error recovery, and permanent error fail-fast handling.
"""

import unittest
from unittest.mock import MagicMock
from database.exceptions import PermanentDatabaseError, TransientDatabaseError
from database.retry import execute_with_retry


class TestReliability(unittest.TestCase):

    def test_successful_execution_without_retry(self):
        """Verify function executes once when no exception occurs."""
        mock_func = MagicMock(return_value="success")
        res = execute_with_retry(mock_func, max_retries=3, initial_delay=0.01)
        self.assertEqual(res, "success")
        self.assertEqual(mock_func.call_count, 1)

    def test_transient_failure_recovery_on_second_attempt(self):
        """Verify retry recovers when transient error occurs on first attempt."""
        mock_func = MagicMock(side_effect=[TransientDatabaseError("Connection timeout"), "success"])
        res = execute_with_retry(
            mock_func,
            max_retries=3,
            initial_delay=0.01,
            retryable_exceptions=(TransientDatabaseError,),
        )
        self.assertEqual(res, "success")
        self.assertEqual(mock_func.call_count, 2)

    def test_exhausted_retries_raises_exception(self):
        """Verify exception raised after exhausting max retries."""
        mock_func = MagicMock(side_effect=TransientDatabaseError("Persistent network outage"))
        with self.assertRaises(TransientDatabaseError):
            execute_with_retry(
                mock_func,
                max_retries=2,
                initial_delay=0.01,
                retryable_exceptions=(TransientDatabaseError,),
            )
        self.assertEqual(mock_func.call_count, 3)  # 1 initial + 2 retries

    def test_permanent_error_fails_fast_without_retrying(self):
        """Verify permanent database error fails fast immediately on first attempt."""
        mock_func = MagicMock(side_effect=PermanentDatabaseError("Syntax error in DDL"))
        with self.assertRaises(PermanentDatabaseError):
            execute_with_retry(mock_func, max_retries=3, initial_delay=0.01)
        self.assertEqual(mock_func.call_count, 1)


if __name__ == "__main__":
    unittest.main()
