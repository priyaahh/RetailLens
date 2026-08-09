"""
connection.py
-------------
Database Connection Management module using SQLAlchemy engine pooling.
Reads configuration from environment variables (.env) and manages database connections.
"""

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def get_db_url() -> str:
    """
    Constructs database connection URL from environment variables.
    Falls back to local SQLite database if Postgres environment variables are missing.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_sslmode = os.getenv("DB_SSLMODE", "require")

    if db_host and db_user and db_password and db_name:
        # PostgreSQL Connection URL
        url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
        logger.info("Constructed PostgreSQL connection URL for host: %s", db_host)
        return url

    logger.warning("PostgreSQL credentials incomplete in environment. Falling back to local SQLite database.")
    return "sqlite:///data/retaillens_local.db"


def get_db_engine(custom_url: Optional[str] = None) -> Engine:
    """
    Creates and returns SQLAlchemy connection engine with connection pooling settings.

    :param custom_url: Optional override database connection URL (e.g. for testing).
    :return: SQLAlchemy Engine instance.
    """
    url = custom_url or get_db_url()

    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})
    else:
        # Connection pooling settings for PostgreSQL
        engine = create_engine(
            url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,  # Asserts connection health before checkout
        )

    logger.info("SQLAlchemy Database Engine initialized successfully.")
    return engine
