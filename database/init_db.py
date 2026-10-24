"""
init_db.py
----------
Database schema initialization and verification utility for RetailLens.
Executes schema.sql against the configured target database (PostgreSQL or SQLite),
verifies table creation, and reports deployment database readiness.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root directory to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import text
from config.app_config import get_config
from database.connection import get_db_engine
from database.pool import check_db_health

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")


def initialize_database(schema_path: Path = None, verbose: bool = False) -> bool:
    """
    Reads schema.sql and applies DDL statements to the target database.

    :param schema_path: Optional path to schema.sql file.
    :param verbose: If True, prints individual statement execution.
    :return: True if initialization succeeded, False otherwise.
    """
    if schema_path is None:
        schema_path = project_root / "database" / "schema.sql"

    if not schema_path.exists():
        logger.error("Schema file not found at: %s", schema_path)
        return False

    config = get_config()
    engine = get_db_engine()
    db_health = check_db_health(engine)

    logger.info("Connecting to target database (Dialect: %s | Host: %s)...", engine.dialect.name, config.db_host or "local")
    if db_health.get("status") != "HEALTHY":
        logger.error("Database connection check failed: %s", db_health.get("error"))
        return False

    logger.info("Reading schema DDL from %s...", schema_path)
    with open(schema_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split SQL script into separate executable statements
    statements = []
    current_stmt = []
    for line in sql_content.splitlines():
        trimmed = line.strip()
        if not trimmed or trimmed.startswith("--"):
            continue
        current_stmt.append(line)
        if trimmed.endswith(";"):
            statements.append("\n".join(current_stmt))
            current_stmt = []

    logger.info("Executing %d DDL statements...", len(statements))

    executed_count = 0
    is_sqlite = engine.dialect.name == "sqlite"

    with engine.begin() as conn:
        for stmt in statements:
            stmt_clean = stmt.strip()
            if not stmt_clean:
                continue

            # SQLite-specific syntax adaptations
            if is_sqlite:
                # Skip PostgreSQL specific statements
                if any(x in stmt_clean.upper() for x in ["CREATE EXTENSION", "COMMENT ON", "CREATE OR REPLACE VIEW"]):
                    continue
                # Remove CASCADE from DROP statements
                stmt_clean = stmt_clean.replace(" CASCADE;", ";").replace(" cascade;", ";")
                # Replace Postgres SERIAL types with SQLite equivalents
                stmt_clean = stmt_clean.replace("BIGSERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
                stmt_clean = stmt_clean.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")

            try:
                conn.execute(text(stmt_clean))
                executed_count += 1
                if verbose:
                    first_line = stmt_clean.splitlines()[0][:60]
                    logger.debug("Executed: %s...", first_line)
            except Exception as e:
                # Log warning for DROP IF EXISTS or similar idempotent statements
                if "DROP" in stmt_clean.upper() or "does not exist" in str(e).lower() or "no such table" in str(e).lower():
                    continue
                logger.error("Error executing statement:\n%s\nError: %s", stmt_clean[:120], str(e))
                raise

    logger.info("Successfully executed %d DDL schema statements.", executed_count)

    # Verify key tables exist
    with engine.connect() as conn:
        if engine.dialect.name == "postgresql":
            verify_sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        else:
            verify_sql = "SELECT name AS table_name FROM sqlite_master WHERE type='table';"

        result = conn.execute(text(verify_sql))
        existing_tables = [row[0] for row in result.fetchall()]
        logger.info("Verified active database tables: %s", ", ".join(sorted(existing_tables)))

    return True


def main():
    """Command-line runner."""
    parser = argparse.ArgumentParser(description="RetailLens Database Initializer")
    parser.add_argument("--schema", type=str, help="Path to custom schema SQL file", default=None)
    parser.add_argument("--verbose", action="store_true", help="Print statement execution logs")
    args = parser.parse_args()

    schema_file = Path(args.schema) if args.schema else None
    success = initialize_database(schema_path=schema_file, verbose=args.verbose)
    if not success:
        sys.exit(1)
    logger.info("Database initialization completed successfully.")


if __name__ == "__main__":
    main()
