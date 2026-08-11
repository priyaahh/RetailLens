"""
test_logging.py
----------------
Unit tests for production logging configuration and SensitiveDataFilter secret masking.
"""

import logging
import unittest
from config.app_config import AppConfig
from config.logging_config import SensitiveDataFilter, setup_logging


class TestLoggingConfig(unittest.TestCase):

    def test_sensitive_data_filter_password_masking(self):
        """Verify SensitiveDataFilter redacts passwords from log records."""
        filter_inst = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Connecting with password='super_secret_pass'",
            args=(),
            exc_info=None,
        )
        filter_inst.filter(record)
        self.assertIn("password='***MASKED***'", record.msg)
        self.assertNotIn("super_secret_pass", record.msg)

    def test_sensitive_data_filter_url_masking(self):
        """Verify SensitiveDataFilter redacts database connection URLs."""
        filter_inst = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Connecting to postgresql://admin:secret123@localhost:5432/mydb",
            args=(),
            exc_info=None,
        )
        filter_inst.filter(record)
        self.assertIn("postgresql://admin:***MASKED***@localhost:5432/mydb", record.msg)
        self.assertNotIn("secret123", record.msg)

    def test_setup_logging_initialization(self):
        """Verify setup_logging configures root logger without exceptions."""
        cfg = AppConfig(app_env="testing", log_level="DEBUG")
        logger = setup_logging(config=cfg)
        self.assertEqual(logger.level, logging.DEBUG)


if __name__ == "__main__":
    unittest.main()
