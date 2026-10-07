"""The AI-written text engine inside the website backend (backend/app/ai) and
how the TrustGraphAI slot uses it. Uses a tiny random text model (no
download), so these tests check the wiring, never detection quality."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import engines
from app.api.ai_detectors import router as ai_detectors_router
from app.services.ai_model import TrustGraphAI
from test_detection_routine import tiny_text_model


@pytest.fixture
def client():
    """Only the AI routes of the website: they need no database."""
    app = FastAPI()
    app.include_router(ai_detectors_router, prefix="/api")
    return TestClient(app)


def test_no_trained_model_gives_the_exact_pending_answer(client):
    text = client.post("/api/text/ai-check", json={"text": "ordinary text"}).json()
    assert text["ai_written_score"] is None and text["available"] is False
    assert text["reasons"] == ["AI-content analysis is pending AI integration; no score was produced."]


def test_trained_text_model_answers_ai_check(client, tmp_path, monkeypatch):
    texts = ["hello there my friend", "as an ai language model i can help", "see you at six tonight"]
    monkeypatch.setenv("AI_TEXT_MODEL_DIR", str(tiny_text_model(tmp_path / "text_model", texts)))
    engines.reset()
    body = client.post("/api/text/ai-check", json={"text": "hello there my friend"}).json()
    assert body["available"] is True and 0.0 <= body["ai_written_score"] <= 1.0
    assert "distilroberta" in body["model"]
    # empty text: nothing to judge, so the pending answer, not a score
    result = TrustGraphAI().analyze("ai_content", {"text": "   "})
    assert result.risk_score is None and result.risk_level == "PENDING"


def test_video_is_not_analysed():
    """The deepfake model was removed: no video route, and video stays a
    pending placeholder that never produces a score."""
    paths = {r.path for r in ai_detectors_router.routes}
    assert paths == {"/text/ai-check"}
    result = TrustGraphAI().analyze("video", {"images": []})
    assert result.risk_score is None and result.risk_level == "PENDING"
