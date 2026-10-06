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

    def test_one_project_static_site_plus_one_python_function(self):
        # No beta "services": a plain project works on every Vercel account.
        self.assertNotIn("services", self.config)
        self.assertEqual(self.config["outputDirectory"], "front end/dist")
        self.assertIn('"front end"', self.config["buildCommand"])
        self.assertIn("api/index.py", self.config["functions"])
        self.assertNotIn("backend/", self.config["functions"]["api/index.py"].get("excludeFiles", ""))
        self.assertFalse((ROOT / "app").exists())
        self.assertTrue((ROOT / "backend/app/main.py").exists())

    def test_function_requirements_match_backend(self):
        def deps(path):
            return sorted(line.strip() for line in (ROOT / path).read_text().splitlines() if line.strip() and not line.startswith("#"))
        self.assertEqual(deps("api/requirements.txt"), deps("backend/requirements.txt"))

    def test_python_entrypoint_imports_from_backend_root_without_root_app(self):
        env = {**os.environ, "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:5432/test"}
        command = "from app.main import app; from fastapi import FastAPI; assert isinstance(app, FastAPI); print('entrypoint OK')"
        result = subprocess.run([sys.executable, "-c", command], cwd=ROOT / "backend", env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("entrypoint OK", result.stdout)

    def test_vercel_function_entrypoint_serves_the_backend_app(self):
        env = {**os.environ, "DATABASE_URL": "postgresql+psycopg://test:test@127.0.0.1:1/test"}
        command = ("import runpy; from fastapi import FastAPI; m = runpy.run_path('api/index.py'); "
                   "assert isinstance(m['app'], FastAPI); assert '/api/detect' in m['app'].openapi()['paths']; print('function OK')")
        result = subprocess.run([sys.executable, "-c", command], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("function OK", result.stdout)

    def target(self, path):
        for rule in self.config["rewrites"]:
            if re.fullmatch(rule["source"], path):
                return rule["destination"]
        return None  # served from the built files (or a 404)

    def test_api_health_and_docs_go_to_the_function(self):
        for path in ("/api/detect", "/api/unknown", "/api/workspace/status", "/health", "/health/database", "/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json"):
            self.assertEqual(self.target(path), "/api/index", path)

    def test_spa_fallback_is_navigation_only(self):
        for path in ("/", "/app/analyze", "/app/analytics", "/app/detections/abc-123", "/login"):
            self.assertEqual(self.target(path), "/index.html", path)
        for path in ("/assets/missing.js", "/favicon.ico", "/.env"):
            self.assertIsNone(self.target(path), path)

    def test_frontend_api_defaults_to_same_origin(self):
        source = (ROOT / "front end/src/config/appConfig.ts").read_text()
        self.assertIn('VITE_API_BASE_URL ?? "/api"', source)
        ignore = (ROOT / ".vercelignore").read_text()
        for path in (".env", "/backup/", "/.venv/", "/models/"):
            self.assertIn(path, ignore.splitlines())
        self.assertIn("/src/", ignore.splitlines())
        self.assertNotIn("src", ignore.splitlines(), "A bare src rule could exclude front end/src")
