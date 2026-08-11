"""
reader.py
---------
Production-grade file reader module responsible for ingesting tabular retail datasets
(CSV and Excel formats) with encoding resilience, file size checks, path sanitization,
and structural header validation.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from config.schema_config import IngestionConfig

# Configure module-level logger
logger = logging.getLogger(__name__)


class DataFileReader:
    """Safely ingests and parses raw tabular datasets into Pandas DataFrames."""

    def __init__(self, config: IngestionConfig = IngestionConfig()):
        self.config = config

    def validate_file_metadata(self, file_path: Union[str, Path]) -> Path:
        """
        Validates path security, file existence, extension, and file size boundaries.

        :param file_path: Absolute or relative path to the target file.
        :return: Validated Path object.
        :raises FileNotFoundError: If the file does not exist.
        :raises ValueError: If extension is unsupported, path is invalid, or file size exceeds limits.
        """
        raw_str = str(file_path)
        if ".." in raw_str:
            error_msg = f"Path traversal characters detected in file path: '{raw_str}'"
            logger.error(error_msg)
            raise ValueError(error_msg)

        path = Path(file_path).resolve()

        # 1. Existence check
        if not path.exists():
            error_msg = f"File not found at specified path: {path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        # 2. Extension check
        ext = path.suffix.lower()
        if ext not in self.config.SUPPORTED_EXTENSIONS:
            error_msg = (
                f"Unsupported file format '{ext}'. "
                f"Allowed formats: {self.config.SUPPORTED_EXTENSIONS}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 3. File size check
        file_size = path.stat().st_size
        if file_size > self.config.MAX_FILE_SIZE_BYTES:
            error_msg = (
                f"File size ({file_size / (1024 * 1024):.2f} MB) exceeds maximum "
                f"allowed threshold ({self.config.MAX_FILE_SIZE_BYTES / (1024 * 1024):.2f} MB)."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("File metadata validated successfully: %s (Size: %d bytes)", path.name, file_size)
        return path

    def read_file(self, file_path: Union[str, Path]) -> pd.DataFrame:
        """
        Reads a CSV or Excel file into a Pandas DataFrame with encoding fallback.

        :param file_path: Path to target data file.
        :return: Ingested Pandas DataFrame.
        :raises ValueError: If column headers are missing or parsing fails.
        """
        path = self.validate_file_metadata(file_path)
        ext = path.suffix.lower()

        df: Optional[pd.DataFrame] = None

        if ext == ".csv":
            df = self._read_csv_with_fallback(path)
        elif ext in [".xlsx", ".xls"]:
            df = self._read_excel(path)

        if df is None or df.empty:
            error_msg = f"File at '{path}' is empty or could not be parsed."
            logger.error(error_msg)
            raise ValueError(error_msg)

        self._validate_header_structure(df)
        logger.info("Successfully ingested %d rows and %d columns from %s", len(df), len(df.columns), path.name)
        return df

    def _read_csv_with_fallback(self, path: Path) -> pd.DataFrame:
        """
        Reads CSV files using multi-encoding fallback to handle legacy/special characters.

        Encodings tried: utf-8 -> latin1 -> iso-8859-1 -> cp1252
        """
        encodings = ["utf-8", "latin1", "iso-8859-1", "cp1252"]

        for encoding in encodings:
            try:
                logger.debug("Attempting to parse CSV file '%s' with encoding '%s'", path.name, encoding)
                df = pd.read_csv(path, encoding=encoding, low_memory=False)
                logger.info("Successfully parsed CSV file '%s' using '%s' encoding.", path.name, encoding)
                return df
            except (UnicodeDecodeError, Exception) as e:
                logger.debug("Failed to read CSV with encoding '%s': %s", encoding, str(e))
                continue

        error_msg = f"Failed to parse CSV file '{path.name}' with any supported encoding."
        logger.error(error_msg)
        raise ValueError(error_msg)

    def _read_excel(self, path: Path) -> pd.DataFrame:
        """Reads Excel (.xlsx/.xls) files into DataFrame."""
        try:
            logger.debug("Parsing Excel file '%s'...", path.name)
            df = pd.read_excel(path, engine="openpyxl" if path.suffix == ".xlsx" else None)
            return df
        except Exception as e:
            error_msg = f"Failed to read Excel file '{path.name}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _validate_header_structure(self, df: pd.DataFrame) -> None:
        """Verifies presence of mandatory columns in DataFrame header."""
        missing_columns = [
            col for col in self.config.REQUIRED_COLUMNS if col not in df.columns
        ]

        if missing_columns:
            error_msg = (
                f"Missing required columns in dataset header: {missing_columns}. "
                f"Expected mandatory columns: {self.config.REQUIRED_COLUMNS}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Dataset header structure validated successfully.")
