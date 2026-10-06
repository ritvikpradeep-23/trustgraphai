"""Load known, labelled fakes into the fingerprint database.

    python scripts/seed_fingerprints.py                    # data/known_fakes/manifest.json
    python scripts/seed_fingerprints.py --manifest my.json
    python scripts/seed_fingerprints.py --demo             # also add the built-in demo items

Manifest: a JSON list, one entry per known fake:
    {"kind": "image", "path": "images/fake1.jpg", "label": "deepfake", "source": "where it came from"}
    {"kind": "text",  "text": "Dear customer, your KYC ...", "label": "scam", "source": "..."}
Image paths are relative to the manifest. Only fingerprints are stored (plus
label and source), never the image or text itself. The database comes from
FINGERPRINT_DB_URL (default sqlite:///data/fingerprints.sqlite3).
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.fingerprint import service as fp  # noqa: E402
from app.fingerprint.store import FingerprintStore  # noqa: E402

DEMO_TEXTS = [
    "Dear customer, your SBI KYC is pending and your account will be blocked today. Share the OTP to verify immediately.",
    "Hi Mum, my phone broke, this is my new number. Please buy 2 Google Play gift cards and send me the codes now.",
]


def demo_image(seed: int = 7, size: int = 320) -> Image.Image:
    """A synthetic stand-in for a known fake (NOT a real deepfake): smooth
    random shapes, so its perceptual hash behaves like a photo's."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    img = np.zeros((size, size, 3))
    for _ in range(12):
        cx, cy, r = rng.random(3) * [1, 1, 0.4] + [0, 0, 0.05]
        blob = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (2 * r * r)))
        img += blob[..., None] * rng.random(3)
    img = (img / img.max() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(img)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--manifest", default=str(ROOT / "data/known_fakes/manifest.json"))
    parser.add_argument("--demo", action="store_true", help="add the built-in demo image and texts")
    args = parser.parse_args()

    settings = get_settings()
    store = FingerprintStore(settings.fingerprint_db_url, settings.fingerprint_full_scan_max)
    added = []
    if args.demo:
        added.append(("image", "demo (synthetic)", fp.add_image(store, demo_image(), "demo-known-fake", "seed --demo")))
        for t in DEMO_TEXTS:
            added.append(("text", t[:40] + "…", fp.add_text(store, t, "demo-known-scam", "seed --demo")))
    manifest = Path(args.manifest)
    if manifest.exists():
        for entry in json.loads(manifest.read_text(encoding="utf-8")):
            label, source = entry.get("label", "known-fake"), entry.get("source", "")
            if entry.get("kind") == "image":
                img = Image.open(manifest.parent / entry["path"]).convert("RGB")
                added.append(("image", entry["path"], fp.add_image(store, img, label, source)))
            elif entry.get("kind") == "text":
                added.append(("text", entry["text"][:40] + "…", fp.add_text(store, entry["text"], label, source)))
    elif not args.demo:
        print(f"No manifest at {manifest}. Add one, or run with --demo.")
    for kind, name, record_id in added:
        print(f"  {kind:5s} {record_id}  {name}")
    print(f"Added {len(added)}. Database now holds {store.count('image')} images and {store.count('text')} texts.")


if __name__ == "__main__":
    main()
