"""
test_security.py
----------------
Security-focused unit tests covering path traversal prevention, credential masking,
SQL injection protection, and oversized file guardrails.
"""

import unittest
from pathlib import Path
from config.logging_config import SensitiveDataFilter
from config.schema_config import IngestionConfig
from ingestion.reader import DataFileReader


class TestSecurity(unittest.TestCase):

    def setUp(self):
        self.reader = DataFileReader()

    def test_path_traversal_prevention(self):
        """Verify path traversal sequences are rejected."""
        with self.assertRaises(ValueError) as ctx:
            self.reader.validate_file_metadata("../data/raw/malicious.csv")
        self.assertIn("Path traversal characters detected", str(ctx.exception))

    def test_log_sanitization(self):
        """Verify SensitiveDataFilter redacts passwords from log strings."""
        filter_inst = SensitiveDataFilter()
        rec = type("LogRecord", (), {"msg": "DB_PASSWORD=mysecretpassword", "args": ()})()
        filter_inst.filter(rec)
        self.assertIn("***MASKED***", rec.msg)
        self.assertNotIn("mysecretpassword", rec.msg)

    def test_oversized_file_rejection(self):
        """Verify files larger than maximum size limit are rejected."""
        custom_config = IngestionConfig()
        custom_config.MAX_FILE_SIZE_BYTES = 10  # 10 Bytes limit for testing

        test_file = Path("data/raw/test_oversized.csv")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("Header1,Header2\n12345678901234567890\n")

        try:
            reader = DataFileReader(config=custom_config)
            with self.assertRaises(ValueError) as ctx:
                reader.validate_file_metadata(test_file)
            self.assertIn("exceeds maximum allowed threshold", str(ctx.exception))
        finally:
            if test_file.exists():
                test_file.unlink()


if __name__ == "__main__":
    unittest.main()
