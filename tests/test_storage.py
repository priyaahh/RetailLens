"""
test_storage.py
---------------
Unit tests for LocalStorageBackend (Phase 7 Milestone 5).
"""

import os
import shutil
import tempfile
import unittest

from storage.local import LocalStorageBackend


class TestLocalStorageBackend(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = LocalStorageBackend(base_dir=self.temp_dir)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_write_read_exists_delete(self):
        """Verify storage write, read, exists, list_files, and delete methods."""
        rel_path = "test_zone/sample.txt"
        content = b"Hello RetailLens Storage Abstraction"

        # 1. Write
        written = self.storage.write(content, rel_path)
        self.assertTrue(written)

        # 2. Exists
        self.assertTrue(self.storage.exists(rel_path))

        # 3. Read
        read_bytes = self.storage.read(rel_path)
        self.assertEqual(read_bytes, content)

        # 4. List Files
        files = self.storage.list_files("test_zone")
        self.assertEqual(len(files), 1)

        # 5. Delete
        deleted = self.storage.delete(rel_path)
        self.assertTrue(deleted)
        self.assertFalse(self.storage.exists(rel_path))


if __name__ == "__main__":
    unittest.main()
