import os
import unittest
import pytest
from unittest.mock import patch

from services.key_management import ApiKeyManager


class TestApiKeyManager(unittest.TestCase):
    """Tests for the ApiKeyManager class, especially the production secret key requirement."""

    def setUp(self):
        """Set up environment for tests."""
        # Clear relevant environment variables before each test
        if "SERVER_SECRET_KEY" in os.environ:
            del os.environ["SERVER_SECRET_KEY"]
        if "RAILWAY_STATIC_URL" in os.environ:
            del os.environ["RAILWAY_STATIC_URL"]
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

    def test_development_environment_no_key(self):
        """In development environments, missing SERVER_SECRET_KEY should generate a temporary key."""
        # Ensure we're in a development environment (no production indicators)
        manager = ApiKeyManager()
        # No exception should be raised, and a secret should be generated
        self.assertIsNotNone(manager.server_secret)

    @patch.dict(os.environ, {"RAILWAY_STATIC_URL": "https://example.railway.app"})
    def test_production_railway_no_key_failure(self):
        """In Railway production, missing SERVER_SECRET_KEY should raise ValueError."""
        # This test simulates a Railway production environment
        with self.assertRaises(ValueError) as context:
            ApiKeyManager()
        self.assertIn("SERVER_SECRET_KEY must be set", str(context.exception))

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_production_env_var_no_key_failure(self):
        """When ENVIRONMENT=production, missing SERVER_SECRET_KEY should raise ValueError."""
        # This test simulates a generic production environment
        with self.assertRaises(ValueError) as context:
            ApiKeyManager()
        self.assertIn("SERVER_SECRET_KEY must be set", str(context.exception))

    @patch.dict(os.environ, {"RAILWAY_STATIC_URL": "https://example.railway.app", 
                            "SERVER_SECRET_KEY": "test_secret_key"})
    def test_production_with_key_success(self):
        """In production with SERVER_SECRET_KEY set, initialization should succeed."""
        # This test ensures the manager initializes correctly in production with a key
        manager = ApiKeyManager()
        self.assertEqual(manager.server_secret, "test_secret_key")

    def test_explicit_server_secret(self):
        """Explicit server_secret parameter should override environment variables."""
        # This tests that explicitly passing a secret in the constructor works
        manager = ApiKeyManager(server_secret="explicit_secret")
        self.assertEqual(manager.server_secret, "explicit_secret")

    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_production_explicit_server_secret(self):
        """In production, explicitly passing a secret should work."""
        # This tests explicit secret in production environment
        manager = ApiKeyManager(server_secret="explicit_secret")
        self.assertEqual(manager.server_secret, "explicit_secret")


if __name__ == "__main__":
    unittest.main() 