"""Tests for the AI engines and the two routines (scam engine, deepfake video,
AI-written text, accuracy + learning routines).

- Every test runs from the project folder, whichever folder pytest was started
  in: the engine loads models/ and data/ relative to the project root.
- Scam tests use standard backend requirements. Only media tests need the
  optional Torch/transformers/OpenCV packages.
"""
import importlib.util
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[2])

AI_PACKAGES = ("sklearn", "pandas", "joblib")
missing = [name for name in AI_PACKAGES if importlib.util.find_spec(name) is None]
if missing:
    print(f"tests/engine skipped: AI packages not installed ({', '.join(missing)}); "
          "pip install -r backend/requirements.txt")
    collect_ignore_glob = ["test_*.py"]
else:
    media_missing = [name for name in ("torch", "transformers", "cv2")
                     if importlib.util.find_spec(name) is None]
    if media_missing:
        collect_ignore = ["test_backend_efficientnet.py", "test_detection_routine.py"]
