"""Backend for trustgraph_extension/test/universal-e2e.js: the real API
(app.main) on 127.0.0.1:<port>, against the PostgreSQL database in
DATABASE_URL, seeded with the demo items (scripts/seed_fingerprints.py --demo:
one known-fake image and two reported scam messages). Also writes the test
assets to --assets: known.png (seeded), other.png (unrelated) and known.webm
(made of the seeded image; needs ffmpeg).

    DATABASE_URL=postgresql+psycopg://...trustgraph_e2e python tests/universal_e2e_server.py --assets /tmp/a

Use a throwaway database: the demo items are added to it.
"""
import argparse
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import uvicorn  # noqa: E402

spec = importlib.util.spec_from_file_location("seed", ROOT / "scripts/seed_fingerprints.py")
seed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seed)


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

    from app.core.database import SessionLocal, create_tables
    from app.fingerprint import service as fp

    create_tables()
    with SessionLocal() as db:
        fp.add_image(db, known, "demo-known-fake", "e2e seed")
        for t in seed.DEMO_TEXTS:
            seed.add_reported_text(db, t)
    print("seeded; serving on", args.port, flush=True)
    uvicorn.run("app.main:app", host="127.0.0.1", port=args.port, log_level="info")


if __name__ == "__main__":
    main()
