"""
cloud.py
--------
Cloud Object Storage Backend Implementation for RetailLens (Phase 8 Milestone 3).
Extends StorageBackend interface to support S3-compatible cloud object storage
with graceful mock fallback for local development and unit testing.
"""

import logging
from typing import List, Optional

from storage.base import StorageBackend

# Check boto3 availability
HAS_BOTO3 = False
try:
    import boto3
    from botocore.exceptions import ClientError
    HAS_BOTO3 = True
except ImportError:
    boto3 = None
    ClientError = Exception

logger = logging.getLogger(__name__)


class CloudStorageBackend(StorageBackend):
    """S3-Compatible Cloud Object Storage Backend Implementation."""

    def __init__(
        self,
        bucket_name: str = "retaillens-data-lake",
        region_name: str = "us-east-1",
        s3_client: Optional[Any] = None,
    ):
        """
        Constructor initializing S3 client.

        :param bucket_name: Cloud object storage bucket name.
        :param region_name: Target cloud region name.
        :param s3_client: Injected S3 client (or mock for unit testing).
        """
        self.bucket_name = bucket_name
        self.region_name = region_name
        self._in_memory_store = {}

        if s3_client is not None:
            self.s3_client = s3_client
        elif HAS_BOTO3:
            try:
                self.s3_client = boto3.client("s3", region_name=region_name)
            except Exception as e:
                logger.warning("Could not initialize boto3 S3 client: %s. Using local cloud mock.", str(e))
                self.s3_client = None
        else:
            logger.info("boto3 is not installed. CloudStorageBackend running in local mock mode.")
            self.s3_client = None

    def write(self, data_bytes: bytes, target_path: str) -> bool:
        """Writes binary bytes to cloud object storage bucket."""
        key = target_path.lstrip("/")
        if self.s3_client:
            try:
                self.s3_client.put_object(Bucket=self.bucket_name, Key=key, Body=data_bytes)
                logger.info("CloudStorageBackend: Uploaded %d bytes to s3://%s/%s", len(data_bytes), self.bucket_name, key)
                return True
            except ClientError as e:
                logger.error("CloudStorageBackend S3 upload failed for '%s': %s", key, str(e))
                return False

        # In-Memory Mock Fallback
        self._in_memory_store[key] = data_bytes
        logger.info("CloudStorageBackend (Mock): Stored %d bytes at 's3://%s/%s'", len(data_bytes), self.bucket_name, key)
        return True

    def read(self, source_path: str) -> bytes:
        """Reads binary bytes from cloud object storage bucket."""
        key = source_path.lstrip("/")
        if self.s3_client:
            try:
                res = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                return res["Body"].read()
            except ClientError as e:
                logger.error("CloudStorageBackend S3 download failed for '%s': %s", key, str(e))
                return b""

        return self._in_memory_store.get(key, b"")

    def exists(self, path: str) -> bool:
        """Checks if object key exists in cloud storage bucket."""
        key = path.lstrip("/")
        if self.s3_client:
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except ClientError:
                return False

        return key in self._in_memory_store

    def list_files(self, prefix: str) -> List[str]:
        """Lists key paths matching directory prefix."""
        prefix_clean = prefix.lstrip("/")
        if self.s3_client:
            try:
                res = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix_clean)
                contents = res.get("Contents", [])
                return [item["Key"] for item in contents]
            except ClientError as e:
                logger.error("CloudStorageBackend list failed for prefix '%s': %s", prefix_clean, str(e))
                return []

        return [k for k in self._in_memory_store.keys() if k.startswith(prefix_clean)]

    def delete(self, path: str) -> bool:
        """Deletes object key from storage bucket."""
        key = path.lstrip("/")
        if self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                return True
            except ClientError as e:
                logger.error("CloudStorageBackend delete failed for '%s': %s", key, str(e))
                return False

        if key in self._in_memory_store:
            del self._in_memory_store[key]
            return True
        return False
