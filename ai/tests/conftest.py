"""Tests for the AI engines and the two routines (scam engine, AI-written text,
accuracy + learning routines).

- Every test runs from the ai/ folder, whichever folder pytest was started in:
  the engine loads models/ and data/ relative to it.
- No model trained on this computer is used unless a test sets one itself.
- Scam tests use standard backend requirements. Only the AI-text tests need the
  optional Torch/transformers packages (pip install -r ai/requirements-ai.txt).
"""
import importlib.util
from pathlib import Path

import pytest

AI_FOLDER = Path(__file__).resolve().parents[1]

AI_PACKAGES = ("sklearn", "pandas", "joblib")
missing = [name for name in AI_PACKAGES if importlib.util.find_spec(name) is None]
if missing:
    print(f"ai/tests skipped: AI packages not installed ({', '.join(missing)}); "
          "pip install -r backend/requirements.txt")
    collect_ignore_glob = ["test_*.py"]
else:
    text_missing = [name for name in ("torch", "transformers")
                    if importlib.util.find_spec(name) is None]
    if text_missing:
        collect_ignore = ["test_ai_text_engine.py", "test_detection_routine.py"]


@pytest.fixture(autouse=True)
def in_ai_folder_without_trained_models(monkeypatch, tmp_path):
    monkeypatch.chdir(AI_FOLDER)
    # The website's scam bridge points the engine at ai/models by absolute path when
    # its tests load it first; these tests expect the plain "models" folder.
    from trustgraph import paths
    monkeypatch.setattr(paths, "DEFAULT_DIR", "models")
    monkeypatch.setenv("AI_TEXT_MODEL_DIR", str(tmp_path / "no_text_model"))
    from app.ai import engines
    engines.reset()
    yield
    engines.reset()
