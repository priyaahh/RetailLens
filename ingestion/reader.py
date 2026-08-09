"""
reader.py
---------
Production-grade file reader module responsible for ingesting tabular retail datasets
(CSV and Excel formats) with encoding resilience, file size checks, and structural header validation.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from config.schema_config import IngestionConfig

# Configure module-level logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class DataFileReader:
    """Safely ingests and parses raw tabular datasets into Pandas DataFrames."""

    def __init__(self, config: IngestionConfig = IngestionConfig()):
        self.config = config

    def validate_file_metadata(self, file_path: Union[str, Path]) -> Path:
        """
        Validates file existence, extension, and file size boundaries.

        :param file_path: Absolute or relative path to the target file.
        :return: Validated Path object.
        :raises FileNotFoundError: If the file does not exist.
        :raises ValueError: If extension is unsupported or file size exceeds limits.
        """
        path = Path(file_path)

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

        :param path: Path object pointing to CSV file.
        :return: Parsed DataFrame.
        """
        encodings = ["utf-8", "latin1", "iso-8859-1", "cp1252"]

        for encoding in encodings:
            try:
                logger.info("Attempting CSV read with encoding: %s", encoding)
                df = pd.read_csv(path, encoding=encoding, low_memory=False)
                logger.info("Successfully parsed CSV using encoding: %s", encoding)
                return df
            except (UnicodeDecodeError, Exception) as e:
                logger.warning("Failed to parse CSV with encoding '%s': %s", encoding, str(e))

        raise ValueError(f"Unable to decode CSV file at '{path}' with supported encodings: {encodings}")

    def _read_excel(self, path: Path) -> pd.DataFrame:
        """
        Reads Excel files (.xlsx, .xls) using openpyxl.

        :param path: Path object pointing to Excel file.
        :return: Parsed DataFrame.
        """
        try:
            logger.info("Parsing Excel file using openpyxl engine...")
            df = pd.read_excel(path, engine="openpyxl")
            return df
        except Exception as e:
            error_msg = f"Failed to parse Excel file at '{path}': {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _validate_header_structure(self, df: pd.DataFrame) -> None:
        """
        Verifies that mandatory columns exist in the DataFrame header.

        :param df: Loaded Pandas DataFrame.
        :raises ValueError: If required columns are missing.
        """
        missing_cols = [col for col in self.config.REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            error_msg = (
                f"Raw dataset header validation failed! Missing required columns: {missing_cols}. "
                f"Present columns: {list(df.columns)}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Structural header validation passed. Required columns present.")
