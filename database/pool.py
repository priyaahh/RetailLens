"""
pool.py
-------
Production Database Connection Pool Manager for RetailLens (Phase 8 Milestone 4).
Provides pooled SQLAlchemy engine creation, pre-ping health checks, connection timeouts,
and transactional safety across PostgreSQL and SQLite databases.
"""

import logging
import time
from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.app_config import get_config

logger = logging.getLogger(__name__)


def create_pooled_engine(db_url: Optional[str] = None) -> Engine:
    """
    Creates a SQLAlchemy engine configured with production connection pooling.

    :param db_url: Database connection URL string.
    :return: Configured SQLAlchemy Engine instance.
    """
    cfg = get_config()
    target_url = db_url or cfg.get_db_url()

    if target_url.startswith("sqlite"):
        logger.info("Initializing SQLite engine for connection URL: '%s'", target_url)
        return create_engine(target_url, connect_args={"check_same_thread": False})

    logger.info(
        "Initializing production PostgreSQL pooled engine (Pool Size: %d, Max Overflow: %d, Timeout: %ds)",
        cfg.db_pool_size,
        cfg.db_max_overflow,
        cfg.db_pool_timeout,
    )
    return create_engine(
        target_url,
        pool_size=cfg.db_pool_size,
        max_overflow=cfg.db_max_overflow,
        pool_timeout=cfg.db_pool_timeout,
        pool_recycle=cfg.db_pool_recycle,
        pool_pre_ping=True,
    )


def check_db_health(engine: Engine) -> Dict[str, Any]:
    """
    Performs database ping healthcheck and measures query response latency.

    :param engine: Target SQLAlchemy Engine.
    :return: Health status dictionary.
    """
    start_ts = time.time()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        latency_ms = round((time.time() - start_ts) * 1000, 2)
        return {
            "status": "HEALTHY",
            "latency_ms": latency_ms,
            "database_type": engine.dialect.name,
        }
    except Exception as e:
        logger.error("Database health check ping failed: %s", str(e))
        return {
            "status": "UNHEALTHY",
            "error": str(e),
            "database_type": engine.dialect.name if engine else "unknown",
        }
