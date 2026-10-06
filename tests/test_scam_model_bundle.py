"""Genuine inference from an isolated upload file set, not a cloud-build claim."""
import fnmatch
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["backend/app/ai/scam_engine.py", "ai/src/trustgraph/pipeline.py",
            "ai/models/anomaly_isolation_forest.joblib", "ai/models/risk_bands.json",
            "ai/data/precedent/reports.json"]
PRIVATE = [".env", "backend/.env", "backup/secrets.sql", "ai/backup/secrets.sql", "data/scam_reports.json",
           "ai/data/scam_reports.json", "data/demo_scam_patterns.json", "ai/data/learning/private.json",
           "ai/data/rounds/round_01.jsonl", "ai/models/candidate/classifier_v1/classifier.joblib",
           "ai/models/text_detector/config.json", "ai/models/efficientnet_head.pt",
           "ai/training/track_a.py", "ai/tests/conftest.py", ".venv/pyvenv.cfg"]


@pytest.fixture
def upload_bundle(tmp_path):
    # Git's ignore matcher exercises gitignore-style parent/negation semantics.
    # Use only .vercelignore as .gitignore in this fresh staging directory.
    shutil.copy2(ROOT / ".vercelignore", tmp_path / ".gitignore")
    listed = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"],
                            cwd=ROOT, capture_output=True, check=True).stdout.decode().split("\0")
    paths = sorted(set(filter(None, [*listed, *REQUIRED, *PRIVATE])))
    checked = subprocess.run(["git", f"--git-dir={ROOT / '.git'}", f"--work-tree={tmp_path}",
                              "-c", "core.excludesFile=NUL", "check-ignore", "--no-index", "--stdin", "-z"],
                             cwd=tmp_path, input="\0".join(paths).encode() + b"\0", capture_output=True)
    assert checked.returncode in {0, 1}, checked.stderr.decode()
    ignored = set(filter(None, checked.stdout.decode().split("\0")))
    config = json.loads((ROOT / "vercel.json").read_text())
    pattern = config["functions"]["api/index.py"]["excludeFiles"]
    # This project's brace list contains simple root-relative globs only.
    assert pattern.startswith("{") and pattern.endswith("}")
    excluded = pattern[1:-1].split(",")
    selected = {p for p in paths if p not in ignored and not any(fnmatch.fnmatchcase(p, g) for g in excluded)}
    assert set(REQUIRED) <= selected
    assert not set(PRIVATE) & selected
    for relative in selected:
        source = ROOT / relative
        if source.is_file():
            destination = tmp_path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    return tmp_path


def run_probe(bundle, command):
    # No original source path, candidate flags, real database DSN or .env.
    env = {k: v for k, v in os.environ.items() if not k.startswith(("TRUSTGRAPH_", "PYTHONPATH", "DATABASE_URL", "POSTGRES_URL"))}
    env["DATABASE_URL"] = "postgresql+psycopg://test:test@127.0.0.1:1/test"
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run([sys.executable, "-I", "-c", command], cwd=bundle, env=env,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_isolated_bundle_runs_real_model_through_api(upload_bundle):
    queries = json.loads((ROOT / "data/demo_scam_model_queries.json").read_text())
    command = """
import sys
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path.cwd() / 'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db
from app.api import detect
from app.ai import scam_engine
app.dependency_overrides[get_db] = lambda: Mock()
# Exercise the unmatched-record branch, never patch model inference.
detect.find_previous_report_matches = lambda *a, **k: []
client = TestClient(app)
assert client.get('/health/scam-model').json()['inference'] == 'verified'
import trustgraph
assert Path(trustgraph.__file__).is_relative_to(Path.cwd())
assert scam_engine.ROOT == Path.cwd()
for index, query in enumerate(QUERIES):
    response = client.post('/api/detect', json={'channel': 'other', 'text': query['text']})
    assert response.status_code == 200
    answer = response.json()
    assert answer['method'] == 'original-scam-engine'
    assert answer['model_used'] and answer['decision_source'] == 'model'
    assert answer['risk_level'] in ({'HIGH', 'CAUTION'} if index < 6 else {'LOW'})
    assert answer['signals']['anomaly'] is not None
print('8 real model API checks passed in isolated upload bundle')
""".replace("QUERIES", repr(queries))
    assert "8 real model API checks passed" in run_probe(upload_bundle, command)


@pytest.mark.parametrize("missing", ["ai/models/anomaly_isolation_forest.joblib", "ai/data/precedent/reports.json", "ai/models/risk_bands.json"])
def test_missing_runtime_artifact_fails_health_without_fabricated_score(upload_bundle, missing):
    (upload_bundle / missing).unlink()
    assert "unavailable verified" in run_probe(upload_bundle, """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'backend'))
from fastapi.testclient import TestClient
from app.main import app
from app.ai.scam_engine import analyze
assert analyze('Send your password and OTP immediately') is None
response = TestClient(app).get('/health/scam-model')
assert response.status_code == 503 and not response.json()['ok']
print('unavailable verified')
""")
