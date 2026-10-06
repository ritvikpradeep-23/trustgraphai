"""The website tests check the answers given when NO trained AI model is
present. Point the AI engines at a folder that doesn't exist, so a model
trained on this computer (ai/models/text_detector, ai/models/efficientnet_head.pt)
can't change those answers. Tests that want a model set these themselves."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def no_trained_ai_models(monkeypatch, tmp_path):
    monkeypatch.chdir(ROOT)  # the AI tests switch to ai/; website tests run from the repository root
    # API fallback tests remain deterministic even if optional scam dependencies
    # are installed locally. Model-specific tests override this patch themselves.
    monkeypatch.setattr("app.api.detect.scam_analyze", lambda *args: None)
    from app.ai import engines
    monkeypatch.setenv("AI_TEXT_MODEL_DIR", str(tmp_path / "no_text_model"))
    monkeypatch.setenv("EFFICIENTNET_HEAD_PATH", str(tmp_path / "no_head.pt"))
    engines.reset()
    yield
    engines.reset()
