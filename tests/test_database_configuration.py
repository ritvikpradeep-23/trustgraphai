"""Deployment configuration checks use dummy URLs, never a real database."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from app.core.database import _database_url, engine

ROOT = Path(__file__).resolve().parents[1]


class DatabaseConfigurationTests(unittest.TestCase):
    def test_hosted_url_formats_use_installed_psycopg(self):
        for prefix in ("postgres://", "postgresql://", "postgresql+psycopg://"):
            with self.subTest(prefix=prefix), patch.dict(
                os.environ, {"DATABASE_URL": prefix + "dummy:dummy@localhost/test"}, clear=True
            ):
                self.assertEqual(_database_url(), "postgresql+psycopg://dummy:dummy@localhost/test")

    def test_primary_variable_wins_and_postgres_url_is_fallback(self):
        with patch.dict(os.environ, {"POSTGRES_URL": "postgres://dummy@localhost/fallback"}, clear=True):
            self.assertEqual(_database_url(), "postgresql+psycopg://dummy@localhost/fallback")
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://dummy@localhost/primary",
            "POSTGRES_URL": "postgres://dummy@localhost/fallback",
        }, clear=True):
            self.assertEqual(_database_url(), "postgresql+psycopg://dummy@localhost/primary")
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_database_url())

    def test_engine_rechecks_pooled_connections(self):
        self.assertTrue(engine.pool._pre_ping)

    def test_legacy_shim_uses_relocated_backend_and_sanitizes_errors(self):
        code = """
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch
root = Path.cwd()
sys.path.insert(0, str(root / "backend"))
import app.core.database as db
spec = importlib.util.spec_from_file_location("vercel_compat", root / "api/index.py")
module = importlib.util.module_from_spec(spec)
with patch.object(db, "create_tables", side_effect=RuntimeError("SECRET_DSN_SENTINEL")) as create:
    spec.loader.exec_module(module)
    create.assert_called_once()
from fastapi import FastAPI
assert isinstance(module.app, FastAPI)
print("shim OK")
"""
        env = {**os.environ, "DATABASE_URL": "postgresql://dummy:dummy@127.0.0.1:5432/test"}
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env,
                                capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("shim OK", result.stdout)
        self.assertIn("RuntimeError", result.stderr)
        self.assertNotIn("SECRET_DSN_SENTINEL", result.stderr)
