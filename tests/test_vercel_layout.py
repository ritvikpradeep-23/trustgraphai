"""Source/layout contract tests, not a substitute for a Vercel cloud build."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class VercelLayoutTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "vercel.json").read_text())

    def test_one_project_has_both_services_and_canonical_backend(self):
        self.assertEqual(set(self.config["services"]), {"frontend", "backend"})
        self.assertEqual(self.config["services"]["frontend"]["root"], "front end/")
        self.assertEqual(self.config["services"]["backend"]["root"], "backend/")
        self.assertFalse((ROOT / "app").exists())
        self.assertTrue((ROOT / "backend/app/main.py").exists())
        self.assertTrue((ROOT / "backend/requirements.txt").exists())

    def test_python_entrypoint_imports_from_backend_root_without_root_app(self):
        env = {**os.environ, "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:5432/test"}
        command = "from app.main import app; from fastapi import FastAPI; assert isinstance(app, FastAPI); print('entrypoint OK')"
        result = subprocess.run([sys.executable, "-c", command], cwd=ROOT / "backend", env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("entrypoint OK", result.stdout)

    def test_api_health_and_docs_route_before_frontend_without_prefix_strip(self):
        rules = self.config["rewrites"]
        def target(path):
            for rule in rules:
                pattern = re.escape(rule["source"]).replace(re.escape("/:path*"), "(?:/.*)?")
                if re.fullmatch(pattern, path):
                    self.assertNotIn("path", rule["destination"])
                    return rule["destination"]["service"]
        for path in ("/api/detect", "/api/unknown", "/health", "/health/database", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"):
            self.assertEqual(target(path), "backend", path)
        for path in ("/", "/app/analyze", "/app/analytics", "/login", "/assets/index.js"):
            self.assertEqual(target(path), "frontend", path)

    def test_spa_fallback_is_navigation_only(self):
        rule = self.config["services"]["frontend"]["rewrites"][0]
        self.assertEqual(rule["destination"], "/index.html")
        for path in ("/", "/app/analyze", "/app/analytics", "/login"):
            self.assertIsNotNone(re.fullmatch(rule["source"], path))
        for path in ("/assets/missing.js", "/favicon.ico", "/.env"):
            self.assertIsNone(re.fullmatch(rule["source"], path))

    def test_frontend_api_defaults_to_same_origin(self):
        source = (ROOT / "front end/src/config/appConfig.ts").read_text()
        self.assertIn('VITE_API_BASE_URL ?? "/api"', source)
        ignore = (ROOT / ".vercelignore").read_text()
        for path in (".env", "/backup/", "/.venv/", "/models/"):
            self.assertIn(path, ignore.splitlines())
        self.assertIn("/src/", ignore.splitlines())
        self.assertNotIn("src", ignore.splitlines(), "A bare src rule could exclude front end/src")
