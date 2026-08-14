"""
base.py
-------
Abstract Storage Backend Interface for RetailLens (Phase 7 Milestone 5).
Defines cloud-agnostic storage abstraction methods (write, read, exists, list_files, delete)
allowing seamless switching between local filesystem storage and cloud object storage (AWS S3 / GCP GCS).
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class StorageBackend(ABC):
    """Abstract Base Class for Data Lake Storage Backends."""

    @abstractmethod
    def write(self, data_bytes: bytes, target_path: str) -> bool:
        """Writes binary data to destination storage path."""
        pass

    @abstractmethod
    def read(self, source_path: str) -> bytes:
        """Reads binary data from storage path."""
        pass

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Checks if a file or key exists in storage."""
        pass

    @abstractmethod
    def list_files(self, prefix: str) -> List[str]:
        """Lists file paths matching directory prefix."""
        pass

    @abstractmethod
    def delete(self, path: str) -> bool:
        """Deletes file at target storage path."""
        pass
