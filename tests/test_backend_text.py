import hashlib
import json
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.scam_engine.embedder import Embedder, EmbeddingUnavailable
from app.scam_engine.repository import InMemoryReportRepository
from app.scam_engine.service import normalize_text, risk_level

# The bank-suspension example and a reworded version: same scam, different words.
BANK_SCAM = ("Dear customer, your Lotus Bank account has been suspended due to unusual activity. Verify your "
             "identity within 24 hours at the link below or your account will be permanently closed.")
BANK_SCAM_REWORDED = ("Lotus Bank alert: we have temporarily blocked your account after suspicious logins. Confirm "
                      "your details in the next 24 hours using this link to avoid permanent closure.")
NORMAL = "Dinner at 8?"


class FakeEmbedder:
    """Stand-in for the real model in tests: hashes each word into one of 256
    slots. Shared words -> similar vectors. Only for testing the plumbing."""
    is_loaded = True

    def embed(self, texts):
        out = np.zeros((len(texts), 256), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in re.findall(r"\w+", t.lower()):
                out[i, int(hashlib.md5(w.encode()).hexdigest(), 16) % 256] += 1
            out[i] /= max(np.linalg.norm(out[i]), 1e-9)
        return out


@pytest.fixture
def client(tmp_path):
    settings = Settings(reports_path=str(tmp_path / "reports.json"))
    return TestClient(create_app(settings, embedder=FakeEmbedder()))


def test_report_then_analyze_finds_it_without_leaking_text(client):
    r = client.post("/api/text/report", json={"text": BANK_SCAM, "source": "website"})
    assert r.status_code == 201 and r.json()["status"] == "stored"
    report_id = r.json()["id"]

    a = client.post("/api/text/analyze", json={"text": BANK_SCAM, "source": "extension"}).json()
    assert a["risk_level"] == "HIGH" and a["top_similarity"] > 0.99
    assert a["similar_reports"] == 1
    assert a["matches"] == [{"id": report_id, "similarity": a["top_similarity"], "source": "website"}]
    # Privacy: no part of the stored report comes back.
    assert "Lotus" not in json.dumps(a) and "suspended" not in json.dumps(a)


def test_unrelated_message_is_low_with_no_evidence(client):
    client.post("/api/text/report", json={"text": BANK_SCAM, "source": "website"})
    a = client.post("/api/text/analyze", json={"text": NORMAL, "source": "website"}).json()
    assert a["risk_level"] == "LOW" and a["matches"] == [] and a["similar_reports"] == 0


def test_empty_store_is_low(client):
    a = client.post("/api/text/analyze", json={"text": BANK_SCAM, "source": "website"}).json()
    assert a == {"risk_level": "LOW", "top_similarity": 0.0, "similar_reports": 0, "matches": []}


def test_analyzed_text_is_not_stored(client):
    client.post("/api/text/analyze", json={"text": BANK_SCAM, "source": "website"})
    assert client.get("/health").json()["reports_stored"] == 0


def test_reports_survive_a_restart(tmp_path):
    settings = Settings(reports_path=str(tmp_path / "reports.json"))
    first = TestClient(create_app(settings, embedder=FakeEmbedder()))
    first.post("/api/text/report", json={"text": BANK_SCAM, "source": "website"})
    second = TestClient(create_app(settings, embedder=FakeEmbedder()))  # fresh app reads the file
    assert second.get("/health").json()["reports_stored"] == 1
    assert second.post("/api/text/analyze", json={"text": BANK_SCAM, "source": "x"}).json()["risk_level"] == "HIGH"


def test_bad_requests_get_clear_errors(tmp_path):
    settings = Settings(reports_path=str(tmp_path / "r.json"), max_text_chars=50)
    client = TestClient(create_app(settings, embedder=FakeEmbedder()))
    assert client.post("/api/text/analyze", json={"text": "x" * 51, "source": "w"}).json()["error"] == "text_too_long"
    assert client.post("/api/text/analyze", json={"text": "​  ", "source": "w"}).json()["error"] == "empty_text"
    r = client.post("/api/text/analyze", json={"source": "w"})
    assert r.status_code == 422 and r.json()["error"] == "invalid_request"


def test_missing_model_is_a_503_not_a_crash(tmp_path):
    class Broken:
        is_loaded = False

        def embed(self, texts):
            raise EmbeddingUnavailable("could not load model: OSError")
    client = TestClient(create_app(Settings(reports_path=str(tmp_path / "r.json")), embedder=Broken()))
    r = client.post("/api/text/analyze", json={"text": "hello", "source": "w"})
    assert r.status_code == 503 and r.json()["error"] == "embedding_model_unavailable"


def test_thresholds_map_to_levels():
    s = Settings(scam_high_threshold=0.82, scam_medium_threshold=0.68)
    assert [risk_level(x, s) for x in (0.9, 0.82, 0.75, 0.68, 0.5)] == ["HIGH", "HIGH", "MEDIUM", "MEDIUM", "LOW"]


def test_normalize_removes_invisible_and_lookalike_characters():
    assert normalize_text("Ｖｅｒｉｆｙ​  your\n account") == "Verify your account"


def test_repository_search_orders_by_similarity(tmp_path):
    repo = InMemoryReportRepository(str(tmp_path / "r.json"))
    a, b = np.array([1, 0], np.float32), np.array([0.6, 0.8], np.float32)
    ra, rb = repo.add("a", "s", a), repo.add("b", "s", b)
    hits = repo.search(np.array([1, 0], np.float32), k=2)
    assert [r.id for r, _ in hits] == [ra.id, rb.id] and hits[0][1] == pytest.approx(1.0)


def test_real_model_scores_reworded_scam_well_above_normal_message(tmp_path):
    """Uses the real all-MiniLM-L6-v2 model. Skipped if it can't be downloaded."""
    embedder = Embedder(Settings().embedding_model_name)
    try:
        embedder.embed(["warm-up"])
    except EmbeddingUnavailable as exc:
        pytest.skip(f"embedding model not available here: {exc}")
    client = TestClient(create_app(Settings(reports_path=str(tmp_path / "r.json")), embedder=embedder))
    client.post("/api/text/report", json={"text": BANK_SCAM, "source": "website"})
    reworded = client.post("/api/text/analyze", json={"text": BANK_SCAM_REWORDED, "source": "website"}).json()
    normal = client.post("/api/text/analyze", json={"text": NORMAL, "source": "website"}).json()
    print(f"reworded: {reworded['risk_level']} {reworded['top_similarity']}; normal: {normal['risk_level']} "
          f"{normal['top_similarity']}")
    assert reworded["top_similarity"] > normal["top_similarity"] + 0.3
    assert normal["risk_level"] == "LOW"
