"""
test_compute_router.py
-----------------------
Unit tests for ComputeRouter (Phase 7 Milestone 3).
"""

import os
import tempfile
import unittest
from typing import Any

from ingestion.compute_router import ComputeRouter


class TestComputeRouter(unittest.TestCase):

    def setUp(self):
        self.router = ComputeRouter(default_engine="auto", spark_threshold_mb=100.0)

    def test_explicit_pandas_selection(self):
        """Verify explicit pandas selection returns pandas."""
        engine, size = self.router.select_engine("non_existent.csv", engine_override="pandas")
        self.assertEqual(engine, "pandas")

    def test_auto_small_file_selection(self):
        """Verify small file selects pandas in auto mode."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(b"header1,header2\nval1,val2\n")
            tmp_path = tmp.name

        try:
            engine, size = self.router.select_engine(tmp_path, engine_override="auto")
            self.assertEqual(engine, "pandas")
            self.assertLess(size, 1.0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
