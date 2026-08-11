"""
logging_config.py
-----------------
Production Logging & Observability Configuration Module for RetailLens.
Configures structured console and rotating file log handlers, standardized formatting,
log level controls based on AppConfig, and sensitive data masking filters.
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config.app_config import AppConfig, get_config


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that intercepts log records and redacts sensitive credentials,
    passwords, secret keys, or connection parameters from log messages.
    """

    # Regex patterns matching passwords and sensitive parameter strings
    PATTERNS = [
        (re.compile(r"(password=)['\"][^'\"]+['\"]", re.IGNORECASE), r"\1'***MASKED***'"),
        (re.compile(r"(postgresql://[^:]+:)[^@]+(@)", re.IGNORECASE), r"\1***MASKED***\2"),
        (re.compile(r"(secret_key=)['\"][^'\"]+['\"]", re.IGNORECASE), r"\1'***MASKED***'"),
        (re.compile(r"(DB_PASSWORD=)[^\s]+", re.IGNORECASE), r"\1***MASKED***"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Applies sanitization rules to the log record message."""
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            # Handle formatted logging arguments if present
            new_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern, replacement in self.PATTERNS:
                        arg = pattern.sub(replacement, arg)
                new_args.append(arg)
            record.args = tuple(new_args)
        return True


def setup_logging(
    config: Optional[AppConfig] = None, log_file_path: Optional[str] = None
) -> logging.Logger:
    """
    Initializes application-wide structured logging handlers.

    :param config: Optional AppConfig instance. Uses get_config() if None.
    :param log_file_path: Optional override log file path.
    :return: Root logger instance.
    """
    app_cfg = config or get_config()
    log_level = getattr(logging, app_cfg.log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicated logs
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Standardized Production Log Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(name)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Sensitive Data Filter Instance
    sensitive_filter = SensitiveDataFilter()

    # 1. Console Stream Handler (Stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    root_logger.addHandler(console_handler)

    # 2. Rotating File Handler (logs/retaillens.log)
    if log_file_path is None:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = str(log_dir / "retaillens.log")

    try:
        file_handler = RotatingFileHandler(
            filename=log_file_path,
            maxBytes=5 * 1024 * 1024,  # 5 MB per file
            backupCount=3,              # Retain 3 historical backups
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(sensitive_filter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        root_logger.warning("Failed to initialize RotatingFileHandler: %s", str(e))

    logging.info(
        "Logging system initialized. Profile: '%s' | Level: '%s'",
        app_cfg.app_env,
        app_cfg.log_level,
    )
    return root_logger
