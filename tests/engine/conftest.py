"""Tests for the AI engines and the two routines (scam engine, deepfake video,
AI-written text, accuracy + learning routines).

- Every test runs from the project folder, whichever folder pytest was started
  in: the engine loads models/ and data/ relative to the project root.
- They need the AI packages (pip install -r requirements-ai.txt). Without them
  this folder is skipped, so the website's own tests still run on their own.
"""
import importlib.util
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[2])

AI_PACKAGES = ("sklearn", "pandas", "joblib", "torch", "transformers", "cv2")
missing = [name for name in AI_PACKAGES if importlib.util.find_spec(name) is None]
if missing:
    print(f"tests/engine skipped: AI packages not installed ({', '.join(missing)}); "
          "pip install -r requirements-ai.txt")
    collect_ignore_glob = ["test_*.py"]
