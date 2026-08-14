"""
local.py
--------
Local Filesystem Storage Backend Implementation for RetailLens (Phase 7 Milestone 5).
Implements StorageBackend interface using standard Python pathlib operations.
"""

import logging
import os
from pathlib import Path
from typing import List

from storage.base import StorageBackend

logger = logging.getLogger(__name__)


class LocalStorageBackend(StorageBackend):
    """Local Filesystem Storage Backend Implementation."""

    def __init__(self, base_dir: str = "."):
        """
        Constructor setting up base directory root.

        :param base_dir: Base directory path for file operations.
        """
        self.base_dir = Path(base_dir)

    def write(self, data_bytes: bytes, target_path: str) -> bool:
        """Writes binary data to local file path."""
        try:
            full_path = self.base_dir / target_path
            os.makedirs(full_path.parent, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(data_bytes)
            logger.info("LocalStorageBackend: Wrote %d bytes to '%s'", len(data_bytes), full_path)
            return True
        except Exception as e:
            logger.error("LocalStorageBackend: Write failed for '%s': %s", target_path, str(e))
            return False

    def read(self, source_path: str) -> bytes:
        """Reads binary bytes from local file path."""
        try:
            full_path = self.base_dir / source_path
            with open(full_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error("LocalStorageBackend: Read failed for '%s': %s", source_path, str(e))
            return b""

    def exists(self, path: str) -> bool:
        """Checks if local file path exists."""
        full_path = self.base_dir / path
        return full_path.exists()

    def list_files(self, prefix: str) -> List[str]:
        """Lists all files matching local directory prefix."""
        prefix_path = self.base_dir / prefix
        if not prefix_path.exists():
            return []

        if prefix_path.is_file():
            return [str(prefix_path.relative_to(self.base_dir))]

        return [
            str(p.relative_to(self.base_dir))
            for p in prefix_path.glob("**/*")
            if p.is_file()
        ]

    def delete(self, path: str) -> bool:
        """Deletes file at local storage path."""
        try:
            full_path = self.base_dir / path
            if full_path.exists():
                full_path.unlink()
                logger.info("LocalStorageBackend: Deleted file '%s'", full_path)
                return True
            return False
        except Exception as e:
            logger.error("LocalStorageBackend: Delete failed for '%s': %s", path, str(e))
            return False
