"""The single local service: scam check (/api/score), AI-text check, accuracy
results, and video frames spread over the whole video. No downloads: the
AI-text model is a tiny random one, so only the wiring is checked."""
import csv

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

import detection_common
import run_cycle
from app.config import Settings
from app.deepfake_engine.frame_extractor import extract_evenly, extract_frames
from app.main import create_app
from tests.test_detection_routine import tiny_text_model
from trustgraph.web.server import score as website_score

MESSAGE = {"message_text": "URGENT: your bank account is locked, share the OTP now", "channel": "whatsapp"}


class NoEmbedder:
    is_loaded = False


def client_for(tmp_path, **settings) -> TestClient:
    settings.setdefault("ai_text_model_dir", "")  # never pick up a real trained model from models/
    return TestClient(create_app(Settings(reports_path=str(tmp_path / "r.json"), **settings), embedder=NoEmbedder()))


@pytest.fixture
def text_model(tmp_path):
    return tiny_text_model(tmp_path / "text_model", ["share the otp now", "see you at lunch", "certainly here is"])


# ---------------------------------------------------------------- scam check, same as run_website.py
def test_page_and_examples_are_served(tmp_path):
    client = client_for(tmp_path)
    page = client.get("/")
    assert page.status_code == 200 and "text/html" in page.headers["content-type"] and b"<html" in page.content.lower()
    examples = client.get("/api/examples").json()
    assert examples and {"name", "kind", "interaction"} <= set(examples[0])


def test_score_matches_the_website_and_the_extension_shape(tmp_path):
    body = client_for(tmp_path).post("/api/score", json=MESSAGE).json()
    expected = website_score(dict(MESSAGE))
    assert body["band"] == expected["band"] and body["score"] == pytest.approx(expected["score"])
    # What the extension's normalizeRemote() needs: band, explanation text, signals list.
    assert body["band"] in ("Low", "Caution", "High") and isinstance(body["explanation"], str)
    assert isinstance(body["signals"], list) and "ai_written" not in body  # no AI-text model configured


def test_score_rejects_a_non_object_body(tmp_path):
    r = client_for(tmp_path).post("/api/score", json=["not", "an", "object"])
    assert r.status_code == 422 and r.json()["error"] == "invalid_request"


# ---------------------------------------------------------------- AI-written text
def test_ai_check_without_a_model_is_503_never_a_score(tmp_path):
    client = client_for(tmp_path)
    r = client.post("/api/text/ai-check", json={"text": "hello there"})
    assert r.status_code == 503 and r.json()["error"] == "model_not_configured"
    assert client.get("/health").json()["ai_text_model"] == "not_configured"


def test_ai_check_and_ai_written_field_with_a_model(tmp_path, text_model):
    client = client_for(tmp_path, ai_text_model_dir=str(text_model))
    assert client.get("/health").json()["ai_text_model"] == "configured"
    body = client.post("/api/text/ai-check", json={"text": "certainly here is the otp"}).json()
    assert body["result"] in ("likely_ai", "likely_human") and 0 <= body["ai_score"] <= 1
    scored = client.post("/api/score", json=MESSAGE).json()
    assert scored["ai_written"]["result"] in ("likely_ai", "likely_human") and "band" in scored


def test_ai_check_rejects_too_long_text(tmp_path, text_model):
    client = client_for(tmp_path, ai_text_model_dir=str(text_model), max_text_chars=10)
    r = client.post("/api/text/ai-check", json={"text": "x" * 11})
    assert r.status_code == 422 and r.json()["error"] == "text_too_long"


# ---------------------------------------------------------------- accuracy results
def test_accuracy_before_and_after_a_run(tmp_path, monkeypatch):
    monkeypatch.setattr(run_cycle, "HISTORY", tmp_path / "history.csv")
    monkeypatch.setattr(detection_common, "SPLITS_DIR", tmp_path / "splits")
    client = client_for(tmp_path)
    empty = client.get("/api/accuracy").json()
    assert empty["video"] == {"latest": None, "runs": 0, "unused_batches": None} and "not real-world" in empty["note"]

    with open(tmp_path / "history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=run_cycle.HISTORY_FIELDS)
        w.writeheader()
        w.writerow({"run_at": "2026-10-06T02:00:00", "detector": "text", "batch": "batch_003", "n": 200,
                    "accuracy": "0.8750", "precision": "0.9", "recall": "0.85", "f1": "0.8600", "roc_auc": "",
                    "tn": 90, "fp": 10, "fn": 15, "tp": 85, "model": "abc123", "note": ""})
    text = client.get("/api/accuracy").json()["text"]
    assert text["runs"] == 1 and text["latest"]["accuracy"] == 0.875 and text["latest"]["roc_auc"] is None
    assert text["latest"]["tp"] == 85 and text["latest"]["batch"] == "batch_003"


# ---------------------------------------------------------------- video frames
def numbered_video(path, frames=60, fps=10):
    """Frame i is a flat grey of brightness 4*i, so a frame shows where it came from."""
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (64, 48))
    for i in range(frames):
        writer.write(np.full((48, 64, 3), 4 * i, np.uint8))
    writer.release()
    return path


def test_frames_come_from_the_whole_video_not_just_the_start(tmp_path):
    video = numbered_video(tmp_path / "v.mp4")  # 6 seconds
    frames = extract_frames(str(video), sample_fps=1.0, max_frames=3)  # cap below the 6 seconds
    assert len(frames) == 3
    brightness = [f.mean() for f in frames]
    assert brightness[0] < 20 and brightness[-1] > 200  # first and last part of the clip, not seconds 0-2
    assert len(extract_evenly(str(video), 4)) == 4 and len(extract_evenly(str(video), 500)) == 60
