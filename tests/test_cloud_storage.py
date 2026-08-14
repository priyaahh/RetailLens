"""
test_cloud_storage.py
----------------------
Unit tests for CloudStorageBackend (Phase 8 Milestone 3).
"""

import unittest
from storage.cloud import CloudStorageBackend


class TestCloudStorageBackend(unittest.TestCase):

    def setUp(self):
        self.storage = CloudStorageBackend(bucket_name="test-bucket")

    def test_cloud_storage_mock_operations(self):
        """Verify write, read, exists, list_files, and delete in mock mode."""
        key = "processed/sales_2010.parquet"
        data = b"PAR1_PARQUET_DATA"

        # 1. Write
        self.assertTrue(self.storage.write(data, key))

        # 2. Exists
        self.assertTrue(self.storage.exists(key))

        # 3. Read
        self.assertEqual(self.storage.read(key), data)

        # 4. List Files
        files = self.storage.list_files("processed")
        self.assertEqual(len(files), 1)

        # 5. Delete
        self.assertTrue(self.storage.delete(key))
        self.assertFalse(self.storage.exists(key))


if __name__ == "__main__":
    unittest.main()
