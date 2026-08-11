"""
connection.py
-------------
Database Connection Management module using SQLAlchemy engine pooling.
Reads configuration from environment variables (.env) via centralized AppConfig.
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config.app_config import get_config

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    """
    Constructs database connection URL from environment variables via AppConfig.
    Falls back to local SQLite database if Postgres environment variables are missing.
    """
    config = get_config()
    url = config.get_db_url()
    if url.startswith("postgresql"):
        logger.info("Constructed PostgreSQL connection URL for host: %s", config.db_host)
    return url


def get_db_engine(custom_url: Optional[str] = None) -> Engine:
    """
    Creates and returns SQLAlchemy connection engine with connection pooling settings.

    :param custom_url: Optional override database connection URL (e.g. for testing).
    :return: SQLAlchemy Engine instance.
    """
    config = get_config()
    url = custom_url or get_db_url()

    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        # Connection pooling settings for PostgreSQL from AppConfig
        engine = create_engine(
            url,
            pool_size=config.db_pool_size,
            max_overflow=config.db_max_overflow,
            pool_timeout=config.db_pool_timeout,
            pool_recycle=config.db_pool_recycle,
            pool_pre_ping=True,  # Asserts connection health before checkout
        )

    logger.info("SQLAlchemy Database Engine initialized successfully.")
    return engine
