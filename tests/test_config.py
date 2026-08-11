"""
test_config.py
--------------
Unit tests for AppConfig centralized configuration management and environment validation.
"""

import os
import unittest
from unittest.mock import patch

from config.app_config import AppConfig, ConfigurationError, get_config


class TestAppConfig(unittest.TestCase):

    def test_default_development_config(self):
        """Verify default development configuration settings and fallbacks."""
        with patch.dict(os.environ, {}, clear=True):
            config = AppConfig.load_from_env()
            self.assertEqual(config.app_env, "development")
            self.assertEqual(config.log_level, "INFO")
            self.assertEqual(config.db_port, 5432)
            self.assertEqual(config.max_file_size_mb, 100)
            self.assertEqual(config.cache_ttl_seconds, 300)
            self.assertEqual(config.get_db_url(), "sqlite:///data/retaillens_local.db")

    def test_custom_environment_parsing(self):
        """Verify parsing of explicit custom environment variables."""
        env_vars = {
            "APP_ENV": "testing",
            "LOG_LEVEL": "DEBUG",
            "DB_HOST": "db.example.com",
            "DB_PORT": "5433",
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "test_password",
            "DB_SSLMODE": "disable",
            "MAX_FILE_SIZE_MB": "50",
            "CACHE_TTL_SECONDS": "600",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            config = AppConfig.load_from_env()
            self.assertEqual(config.app_env, "testing")
            self.assertEqual(config.log_level, "DEBUG")
            self.assertEqual(config.db_port, 5433)
            self.assertEqual(config.max_file_size_mb, 50)
            self.assertEqual(config.cache_ttl_seconds, 600)
            self.assertEqual(
                config.get_db_url(),
                "postgresql://test_user:test_password@db.example.com:5433/test_db?sslmode=disable",
            )

    def test_production_strict_validation_missing_db_credentials(self):
        """Verify production environment fails validation when DB credentials are missing."""
        env_vars = {"APP_ENV": "production"}
        with patch.dict(os.environ, env_vars, clear=True):
            with self.assertRaises(ConfigurationError) as ctx:
                AppConfig.load_from_env()
            self.assertIn("missing required database settings", str(ctx.exception))

    def test_production_strict_validation_default_secret_key(self):
        """Verify production environment rejects default insecure SECRET_KEY."""
        env_vars = {
            "APP_ENV": "production",
            "DB_HOST": "db.example.com",
            "DB_NAME": "prod_db",
            "DB_USER": "prod_user",
            "DB_PASSWORD": "secret_password",
            "SECRET_KEY": "default-insecure-dev-key",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            with self.assertRaises(ConfigurationError) as ctx:
                AppConfig.load_from_env()
            self.assertIn("default insecure SECRET_KEY", str(ctx.exception))

    def test_invalid_app_env(self):
        """Verify exception raised for invalid APP_ENV."""
        env_vars = {"APP_ENV": "invalid_env_name"}
        with patch.dict(os.environ, env_vars, clear=True):
            with self.assertRaises(ConfigurationError) as ctx:
                AppConfig.load_from_env()
            self.assertIn("Invalid APP_ENV", str(ctx.exception))

    def test_invalid_db_port(self):
        """Verify exception raised for non-integer or out-of-range DB_PORT."""
        env_vars = {"DB_PORT": "invalid_port"}
        with patch.dict(os.environ, env_vars, clear=True):
            with self.assertRaises(ConfigurationError) as ctx:
                AppConfig.load_from_env()
            self.assertIn("Invalid DB_PORT", str(ctx.exception))

    def test_to_dict_mask_secrets(self):
        """Verify passwords and secret keys are masked in to_dict output."""
        config = AppConfig(db_password="super_secret_password", secret_key="my_secret_key")
        masked_dict = config.to_dict(mask_secrets=True)
        self.assertEqual(masked_dict["db_password"], "***MASKED***")
        self.assertEqual(masked_dict["secret_key"], "***MASKED***")

        unmasked_dict = config.to_dict(mask_secrets=False)
        self.assertEqual(unmasked_dict["db_password"], "super_secret_password")
        self.assertEqual(unmasked_dict["secret_key"], "my_secret_key")


if __name__ == "__main__":
    unittest.main()
