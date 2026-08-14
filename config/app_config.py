"""
app_config.py
-------------
Centralized Production Configuration & Environment Management Module for RetailLens.
Validates environment variables, manages environment profiles (development, testing, production),
enforces safe defaults, and prevents credential leaks.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception raised when application configuration validation fails."""
    pass


@dataclass
class AppConfig:
    """Centralized, immutable application configuration container."""

    # Environment Profile
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "default-insecure-dev-key"

    # Database Settings
    db_host: Optional[str] = None
    db_port: int = 5432
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_sslmode: str = "require"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Distributed & Storage Settings
    storage_backend: str = "local"
    object_storage_bucket: Optional[str] = None
    cloud_region: str = "us-east-1"
    redis_url: Optional[str] = None
    processing_engine: str = "auto"
    spark_threshold_mb: float = 100.0
    metrics_enabled: bool = True

    # Application Performance & Guardrail Settings
    max_file_size_mb: int = 100
    cache_ttl_seconds: int = 300

    @classmethod
    def load_from_env(cls) -> "AppConfig":
        """
        Loads and validates configuration from environment variables.

        :return: Validated AppConfig instance.
        :raises ConfigurationError: If required settings are invalid or missing in production.
        """
        app_env = os.getenv("APP_ENV", "development").lower()
        valid_envs = {"development", "testing", "staging", "production"}
        if app_env not in valid_envs:
            raise ConfigurationError(
                f"Invalid APP_ENV '{app_env}'. Must be one of {sorted(list(valid_envs))}."
            )

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level not in valid_levels:
            raise ConfigurationError(
                f"Invalid LOG_LEVEL '{log_level}'. Must be one of {sorted(list(valid_levels))}."
            )

        # Database Port Validation
        raw_port = os.getenv("DB_PORT", "5432")
        try:
            db_port = int(raw_port)
            if not (1 <= db_port <= 65535):
                raise ValueError("Port out of valid range (1-65535)")
        except ValueError as e:
            raise ConfigurationError(f"Invalid DB_PORT '{raw_port}': {str(e)}")

        # Max File Size Validation
        raw_max_size = os.getenv("MAX_FILE_SIZE_MB", "100")
        try:
            max_file_size_mb = int(raw_max_size)
            if max_file_size_mb <= 0:
                raise ValueError("Must be a positive integer")
        except ValueError as e:
            raise ConfigurationError(f"Invalid MAX_FILE_SIZE_MB '{raw_max_size}': {str(e)}")

        # Cache TTL Validation
        raw_ttl = os.getenv("CACHE_TTL_SECONDS", "300")
        try:
            cache_ttl_seconds = int(raw_ttl)
            if cache_ttl_seconds < 0:
                raise ValueError("Must be non-negative")
        except ValueError as e:
            raise ConfigurationError(f"Invalid CACHE_TTL_SECONDS '{raw_ttl}': {str(e)}")

        # Database Pool Settings Validation
        try:
            db_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
            db_max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
            db_pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
            db_pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
        except ValueError as e:
            raise ConfigurationError(f"Invalid database pool configuration integer: {str(e)}")

        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_sslmode = os.getenv("DB_SSLMODE", "require")
        secret_key = os.getenv("SECRET_KEY", "default-insecure-dev-key")

        config = cls(
            app_env=app_env,
            log_level=log_level,
            secret_key=secret_key,
            db_host=db_host,
            db_port=db_port,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            db_sslmode=db_sslmode,
            db_pool_size=db_pool_size,
            db_max_overflow=db_max_overflow,
            db_pool_timeout=db_pool_timeout,
            db_pool_recycle=db_pool_recycle,
            max_file_size_mb=max_file_size_mb,
            cache_ttl_seconds=cache_ttl_seconds,
        )

        config.validate(strict_db=(app_env in {"production", "staging"}))
        return config

    def validate(self, strict_db: bool = False) -> None:
        """
        Validates configuration consistency.

        :param strict_db: If True, mandates presence of all PostgreSQL credentials.
        :raises ConfigurationError: If mandatory parameters are missing or insecure.
        """
        if strict_db:
            missing = []
            if not self.db_host:
                missing.append("DB_HOST")
            if not self.db_name:
                missing.append("DB_NAME")
            if not self.db_user:
                missing.append("DB_USER")
            if not self.db_password:
                missing.append("DB_PASSWORD")

            if missing:
                raise ConfigurationError(
                    f"Production/Staging environment missing required database settings: {', '.join(missing)}"
                )

            if self.secret_key == "default-insecure-dev-key":
                raise ConfigurationError("Production environment must not use the default insecure SECRET_KEY.")

    def get_db_url(self) -> str:
        """
        Returns constructed database connection URL.
        Falls back to local SQLite database if PostgreSQL credentials are incomplete in non-strict mode.
        """
        if self.db_host and self.db_user and self.db_password and self.db_name:
            return (
                f"postgresql://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}?sslmode={self.db_sslmode}"
            )

        logger.warning(
            "PostgreSQL credentials incomplete in environment (%s). Falling back to local SQLite database.",
            self.app_env,
        )
        return "sqlite:///data/retaillens_local.db"

    def to_dict(self, mask_secrets: bool = True) -> Dict[str, Any]:
        """
        Exports configuration parameters dictionary, optionally masking sensitive passwords and keys.

        :param mask_secrets: If True, replaces passwords with '***MASKED***'.
        :return: Clean dictionary of settings.
        """
        data = {
            "app_env": self.app_env,
            "log_level": self.log_level,
            "secret_key": "***MASKED***" if mask_secrets else self.secret_key,
            "db_host": self.db_host,
            "db_port": self.db_port,
            "db_name": self.db_name,
            "db_user": self.db_user,
            "db_password": "***MASKED***" if (mask_secrets and self.db_password) else self.db_password,
            "db_sslmode": self.db_sslmode,
            "db_pool_size": self.db_pool_size,
            "db_max_overflow": self.db_max_overflow,
            "db_pool_timeout": self.db_pool_timeout,
            "db_pool_recycle": self.db_pool_recycle,
            "max_file_size_mb": self.max_file_size_mb,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }
        return data


# Global cached instance helper
_current_config: Optional[AppConfig] = None


def get_config(reload: bool = False) -> AppConfig:
    """
    Returns global cached AppConfig instance.

    :param reload: If True, reloads configuration from environment.
    :return: Cached AppConfig instance.
    """
    global _current_config
    if _current_config is None or reload:
        _current_config = AppConfig.load_from_env()
    return _current_config
