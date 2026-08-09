"""
schema_config.py
----------------
Configuration module defining data ingestion schema rules, file constraints,
and column data type expectations for the RetailLens data pipeline.
"""

from typing import Dict, List, Set


class IngestionConfig:
    """Configuration constraints for raw file ingestion."""

    # File Ingestion Rules
    MAX_FILE_SIZE_BYTES: int = 100 * 1024 * 1024  # 100 MB Limit
    SUPPORTED_EXTENSIONS: Set[str] = {".csv", ".xlsx", ".xls"}

    # Expected Raw Column Schema
    EXPECTED_COLUMNS: List[str] = [
        "InvoiceNo",
        "StockCode",
        "Description",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
        "CustomerID",
        "Country",
    ]

    # Mandatory Columns (Must not be missing in input file header)
    REQUIRED_COLUMNS: List[str] = [
        "InvoiceNo",
        "StockCode",
        "Quantity",
        "InvoiceDate",
        "UnitPrice",
    ]

    # Schema Data Type Mapping (For Initial Casting Verification)
    COLUMN_TYPES: Dict[str, str] = {
        "InvoiceNo": "string",
        "StockCode": "string",
        "Description": "string",
        "Quantity": "int64",
        "InvoiceDate": "datetime64[ns]",
        "UnitPrice": "float64",
        "CustomerID": "string",
        "Country": "string",
    }
