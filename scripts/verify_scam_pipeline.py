"""Real PostgreSQL/account/model checks in a rolled-back temporary schema.

Public catalog/account data is untouched. Checks records-first ordering, genuine
model inference, all risk bands' persistence and cross-account privacy. Demo
cases are functional fixtures, not an independent accuracy benchmark.
"""
import json
from pathlib import Path
import secrets
import sys
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.ai.scam_engine import analyze, engine as scam_engine
from app.core.accounts import AccountCheck
from app.core.database import Base, engine, get_db
from app.main import app
from scripts.scam_catalog import load_catalog
from scripts.seed_demo_patterns import seed


def run():
    if scam_engine() is None:
        raise RuntimeError("Original scam model unavailable; install requirements-scam.txt")
    patterns = load_catalog()
    queries = json.loads((ROOT / "data/demo_scam_model_queries.json").read_text())
    schema = "tg_scam_verify_" + secrets.token_hex(8)
    with engine.connect() as connection:
        transaction = connection.begin()
        db = None
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            Base.metadata.create_all(connection)
            db = Session(bind=connection, join_transaction_mode="create_savepoint")
            app.dependency_overrides[get_db] = lambda: db
            assert seed(db, patterns) == len(patterns)
            assert seed(db, patterns) == 0
            a, b = TestClient(app), TestClient(app)
            password = secrets.token_urlsafe(24)
            def signup(client, name):
                csrf = client.get("/api/auth/session").json()["csrfToken"]
                result = client.post("/api/auth/register", json={"name": name,
                    "email": name + "@example.invalid", "password": password},
                    headers={"X-CSRF-Token": csrf})
                assert result.status_code == 201
                return {"X-CSRF-Token": result.json()["csrfToken"]}
            headers = signup(a, "scam-verify-a")
            signup(b, "scam-verify-b")
            checked = []
            def check(message):
                response = a.post("/api/workspace/checks", json={"channel": "other", "text": message}, headers=headers)
                assert response.status_code == 200, response.status_code
                result = response.json()
                saved = db.get(AccountCheck, result["detection_id"])
                assert saved is not None and message not in json.dumps(saved.view)
                assert saved.view["riskScore"] == result["risk_score"]
                assert saved.view["riskLevel"] == result["risk_level"]
                assert saved.view["decisionSource"] == result["decision_source"]
                assert saved.view["modelUsed"] == result["model_used"]
                assert a.get("/api/workspace/detections/" + result["detection_id"]).status_code == 200
                assert b.get("/api/workspace/detections/" + result["detection_id"]).status_code == 404
                checked.append(result)
                return result
            with patch("app.api.detect.scam_analyze", side_effect=AssertionError("Model must be skipped")):
                exact = check(patterns[0]["text"])
            assert exact["decision_source"] == "records" and not exact["model_used"]
            assert exact["risk_score"] == 1 and exact["comparison_count"] == len(patterns)
            spy = Mock(wraps=analyze)
            with patch("app.api.detect.scam_analyze", spy):
                for index, query in enumerate(queries):
                    result = check(query["text"])
                    assert result["decision_source"] == "model" and result["model_used"]
                    assert result["previous_report_matches"] == []
                    assert result["risk_level"] in ({"CAUTION", "HIGH"} if index < 6 else {"LOW"})
            assert spy.call_count == len(queries)
            with patch("app.api.detect.scam_analyze", return_value=None):
                unknown = check("A separate test of the unavailable model with no matching catalog entry.")
            assert unknown["risk_level"] == "UNKNOWN" and unknown["risk_score"] is None
            history = a.get("/api/workspace/detections").json()
            assert {row["id"] for row in history} == {r["detection_id"] for r in checked}
            assert {row["riskLevel"] for row in history} == {"HIGH", "CAUTION", "LOW", "UNKNOWN"}
            assert b.get("/api/workspace/detections").json() == []
            print(f"PostgreSQL checks passed: {len(patterns)} unique catalog records; exact match skipped model; {len(queries)} real model fallbacks; HIGH/CAUTION/LOW/UNKNOWN persisted; account isolation and metadata privacy verified.")
        finally:
            if db is not None:
                db.close()
            app.dependency_overrides.clear()
            transaction.rollback()
            print("Temporary schema and all verification rows rolled back; public data untouched.")


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        print(f"Scam pipeline verification failed ({type(error).__name__}); no credentials displayed.")
        sys.exit(1)
