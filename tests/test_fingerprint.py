"""Known-fakes database: a seeded item and a re-compressed copy of it match;
an unrelated item doesn't. Checked at the hash level, in the store, and end
to end through POST /api/score and GET /health/fingerprint."""
import base64
import importlib.util
import io
import sqlite3
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import Settings
from app.fingerprint import hashing
from app.fingerprint import service as fp
from app.fingerprint.store import BAND_QUERY, FingerprintStore
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("seed_fingerprints", ROOT / "scripts/seed_fingerprints.py")
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

KNOWN_TEXT = seed.DEMO_TEXTS[0]
# Same scam, re-typed: case, punctuation and spacing changed.
KNOWN_TEXT_COPY = "DEAR CUSTOMER!!  Your SBI KYC is pending, and your account will be blocked today... share the OTP to verify immediately"
UNRELATED_TEXT = "Lunch at the canteen at one? I will bring the notes for the exam tomorrow."


class FakeEmbedder:
    is_loaded = True

    def embed(self, texts):
        return np.ones((len(texts), 8), dtype=np.float32)


def recompressed(img: Image.Image) -> Image.Image:
    """What a messaging app does to a shared image: smaller, heavy JPEG."""
    small = img.resize((int(img.width * 0.85), int(img.height * 0.85)), Image.Resampling.BILINEAR)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=30)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def known():
    return seed.demo_image(seed=7)


@pytest.fixture
def unrelated():
    return seed.demo_image(seed=99)


@pytest.fixture
def store(tmp_path, known):
    s = FingerprintStore(f"sqlite:///{tmp_path / 'fp.sqlite3'}")
    fp.add_image(s, known, "known-fake", "test")
    fp.add_text(s, KNOWN_TEXT, "known-scam", "test")
    return s


def test_hashes_survive_recompression(known, unrelated):
    copy = recompressed(known)
    assert hashing.hamming(hashing.phash(known), hashing.phash(copy)) <= 10
    assert hashing.hamming(hashing.dhash(known), hashing.dhash(copy)) <= 10
    assert hashing.hamming(hashing.phash(known), hashing.phash(unrelated)) > 10


def test_text_normalisation_and_simhash():
    assert hashing.normalize_text("  Share the O.T.P!!  ") == "share the otp"
    assert hashing.hamming(hashing.simhash(KNOWN_TEXT), hashing.simhash(KNOWN_TEXT_COPY)) <= 6
    assert hashing.hamming(hashing.simhash(KNOWN_TEXT), hashing.simhash(UNRELATED_TEXT)) > 6
    assert hashing.simhash("!!! ...") is None


def test_store_lookup(store, known, unrelated):
    settings = Settings()
    exact = fp.check_image(store, known, settings)
    copy = fp.check_image(store, recompressed(known), settings)
    other = fp.check_image(store, unrelated, settings)
    assert exact["db_match"] and exact["similarity"] == 1.0
    assert copy["db_match"] and copy["matched_record_id"] == exact["matched_record_id"]
    assert not other["db_match"] and other["matched_record_id"] is None
    assert fp.check_text(store, KNOWN_TEXT_COPY, settings)["db_match"]
    assert not fp.check_text(store, UNRELATED_TEXT, settings)["db_match"]


def test_banded_index_finds_close_records_without_a_full_scan(tmp_path, known):
    s = FingerprintStore(f"sqlite:///{tmp_path / 'big.sqlite3'}", full_scan_max=0)  # index only
    record = fp.add_image(s, known, "known-fake")
    h = hashing.phash(known)
    assert s.lookup("image", h ^ 0b101, threshold=10)["matched_record_id"] == record  # 2 bits off
    with sqlite3.connect(s.path) as db:
        plan = " ".join(str(r) for r in db.execute("EXPLAIN QUERY PLAN " + BAND_QUERY, ["image", 1] * 4))
    assert all(f"ix_fp_b{i}" in plan for i in range(4)) and "SCAN fingerprints" not in plan


@pytest.fixture
def client(tmp_path, known):
    db = tmp_path / "api.sqlite3"
    settings = Settings(reports_path=str(tmp_path / "reports.json"), fingerprint_db_url=f"sqlite:///{db}",
                        deepfake_mode="mine", deepfake_model_path="")
    app = create_app(settings, embedder=FakeEmbedder())
    fp.add_image(app.state.fingerprint_store, known, "known-fake", "test")
    fp.add_text(app.state.fingerprint_store, KNOWN_TEXT, "known-scam", "test")
    return TestClient(app)


def test_api_image_match(client, known, unrelated):
    def check(img):
        r = client.post("/api/score", json={"type": "image", "payload": data_url(img), "hostname": "example.com",
                                            "timestamp": 1760000000000, "capture": "direct"})
        assert r.status_code == 200, r.text
        return r.json()

    seeded, copy, other = check(known), check(recompressed(known)), check(unrelated)
    assert seeded["fingerprint"]["db_match"] is True
    assert copy["fingerprint"]["db_match"] is True
    assert copy["fingerprint"]["matched_record_id"] == seeded["fingerprint"]["matched_record_id"]
    assert other["fingerprint"]["db_match"] is False
    # The model's answer is a separate field; with no model configured it says so.
    assert seeded["deepfake"]["result"] == "not_checked"


def test_api_video_frames(client, known, unrelated):
    frames = [{"t": 0.0, "data": data_url(unrelated)}, {"t": 0.5, "data": data_url(recompressed(known))}]
    r = client.post("/api/score", json={"type": "video", "payload": frames, "hostname": "example.com", "timestamp": 1})
    body = r.json()
    assert r.status_code == 200 and body["frames"] == 2 and body["frame_times"] == [0.0, 0.5]
    assert body["fingerprint"]["db_match"] is True and body["fingerprint"]["frames_matched"] == 1


def test_api_text_keeps_score_and_adds_fingerprint(client):
    plain = client.post("/api/score", json={"message_text": UNRELATED_TEXT, "channel": "other"}).json()
    assert {"band", "score", "signals"} <= plain.keys()  # the existing answer is unchanged
    assert plain["fingerprint"]["db_match"] is False
    copy = client.post("/api/score", json={"type": "text", "payload": KNOWN_TEXT_COPY, "message_text": KNOWN_TEXT_COPY,
                                           "channel": "other", "hostname": "example.com", "timestamp": 1}).json()
    assert copy["fingerprint"]["db_match"] is True and "band" in copy


def test_api_rejects_bad_media(client):
    assert client.post("/api/score", json={"type": "image", "payload": "not an image"}).status_code == 422
    assert client.post("/api/score", json={"type": "video", "payload": []}).status_code == 422


def test_health_round_trip_leaves_nothing_behind(client):
    before = client.app.state.fingerprint_store.count()
    body = client.get("/health/fingerprint").json()
    assert body["ok"] is True and body["probe_found"] is True and body["records"] == before
    assert client.app.state.fingerprint_store.count() == before


def test_api_media_uses_existing_model_when_configured(tmp_path, known):
    settings = Settings(reports_path=str(tmp_path / "r.json"), fingerprint_db_url=f"sqlite:///{tmp_path / 'm.sqlite3'}",
                        deepfake_mock=True)
    client = TestClient(create_app(settings, embedder=FakeEmbedder()))
    body = client.post("/api/score", json={"type": "image", "payload": data_url(known)}).json()
    assert body["deepfake"]["frames_examined"] == 1 and body["deepfake"]["mock"] is True
    assert body["fingerprint"]["db_match"] is False  # empty database: separate answer, not blended


def test_unusable_database_never_breaks_checks(tmp_path, known):
    settings = Settings(reports_path=str(tmp_path / "r.json"), fingerprint_db_url="postgres://example/db")
    client = TestClient(create_app(settings, embedder=FakeEmbedder()))
    media = client.post("/api/score", json={"type": "image", "payload": data_url(known)})
    text = client.post("/api/score", json={"message_text": UNRELATED_TEXT, "channel": "other"})
    assert media.status_code == 200 and media.json()["fingerprint"]["available"] is False
    assert text.status_code == 200 and "band" in text.json() and text.json()["fingerprint"]["available"] is False
    assert client.get("/health/fingerprint").json()["ok"] is False
