"""Backend for trustgraph_extension/test/universal-e2e.js.

Starts the real API on 127.0.0.1:<port> with a temporary known-fakes
database seeded with the demo image and texts (scripts/seed_fingerprints.py),
the demo deepfake model (DEEPFAKE_MOCK) and test assets written to --assets:
known.png (seeded), other.png (unrelated) and known.webm (made of the seeded
image; needs ffmpeg).

    python tests/universal_e2e_server.py --assets /tmp/tg-assets --port 8000
"""
import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import cv2  # noqa: E402

if not hasattr(cv2, "CascadeClassifier"):  # some headless OpenCV builds lack it; faces are then never found
    class _NoFaces:
        def __init__(self, *a, **k): pass
        def empty(self): return False
        def detectMultiScale(self, *a, **k): return []
    cv2.CascadeClassifier = _NoFaces

import numpy as np  # noqa: E402
import uvicorn  # noqa: E402

from app.config import Settings  # noqa: E402
from app.fingerprint import service as fp  # noqa: E402
from app.main import create_app  # noqa: E402

spec = importlib.util.spec_from_file_location("seed", ROOT / "scripts/seed_fingerprints.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


class FakeEmbedder:
    is_loaded = True

    def embed(self, texts):
        return np.ones((len(texts), 8), dtype=np.float32)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", required=True)
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    assets = Path(args.assets)
    assets.mkdir(parents=True, exist_ok=True)
    known, other = seed.demo_image(seed=7), seed.demo_image(seed=99)
    known.save(assets / "known.png")
    other.save(assets / "other.png")
    if shutil.which("ffmpeg"):
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(assets / "known.png"), "-t", "6",
                        "-r", "10", "-c:v", "libvpx", "-b:v", "800k", "-pix_fmt", "yuv420p", str(assets / "known.webm")],
                       check=True)
    tmp = Path(tempfile.mkdtemp(prefix="tg-e2e-"))
    settings = Settings(fingerprint_db_url=f"sqlite:///{tmp / 'fp.sqlite3'}", reports_path=str(tmp / "reports.json"),
                        deepfake_mock=True)
    app = create_app(settings, embedder=FakeEmbedder())
    fp.add_image(app.state.fingerprint_store, known, "demo-known-fake", "e2e seed")
    for t in seed.DEMO_TEXTS:
        fp.add_text(app.state.fingerprint_store, t, "demo-known-scam", "e2e seed")
    print("seeded; serving on", args.port, flush=True)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
