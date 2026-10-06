"""Load known, labelled scams and fakes into the PostgreSQL database
(DATABASE_URL, from .env or the environment).

    python scripts/seed_fingerprints.py --demo             # built-in demo items
    python scripts/seed_fingerprints.py                    # data/known_fakes/manifest.json
    python scripts/seed_fingerprints.py --manifest my.json

Two kinds of entry:
  image -> a fingerprint in `fingerprints` (only the hashes, label and source
           are stored, never the image). The extension's image/video checks
           (POST /api/media/check) are matched against these.
  text  -> a submission plus a report in `submissions`/`reports`, exactly as a
           reported scam. The extension's message checks (POST /api/detect,
           previous-report matching) are matched against these.

Manifest: a JSON list, e.g.
    {"kind": "image", "path": "images/fake1.jpg", "label": "deepfake", "source": "fact-check, 2026-09"}
    {"kind": "text",  "text": "Dear customer, your KYC ...", "label": "scam", "source": "user report"}
Image paths are relative to the manifest. Running it twice adds the items twice.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

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


def add_reported_text(db, text: str, report_type: str = "scam", status: str = "confirmed") -> str:
    """A reported scam, stored the same way POST /api/submit + /api/reports would."""
    from app.core.database import ReportRecord, SubmissionRecord

    now = datetime.now(timezone.utc)
    submission_id = f"sub_{uuid4().hex[:12]}"
    db.add(SubmissionRecord(submission_id=submission_id, source="web_app", content_type="text", text=text,
                            user_consent=True, created_at=now))
    db.flush()
    report_id = f"rep_{uuid4().hex[:12]}"
    db.add(ReportRecord(report_id=report_id, submission_id=submission_id, report_type=report_type,
                        status=status, created_at=now))
    db.commit()
    return report_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--manifest", default=str(ROOT / "data/known_fakes/manifest.json"))
    parser.add_argument("--demo", action="store_true", help="add the built-in demo image and scam texts")
    args = parser.parse_args()

    from app.core.database import SessionLocal, create_tables
    from app.fingerprint import service as fp

    create_tables()
    added = []
    with SessionLocal() as db:
        if args.demo:
            added.append(("image", "demo (synthetic)", fp.add_image(db, demo_image(), "demo-known-fake", "seed --demo")))
            for t in DEMO_TEXTS:
                added.append(("text", t[:40] + "…", add_reported_text(db, t)))
        manifest = Path(args.manifest)
        if manifest.exists():
            for entry in json.loads(manifest.read_text(encoding="utf-8")):
                if entry.get("kind") == "image":
                    img = Image.open(manifest.parent / entry["path"]).convert("RGB")
                    added.append(("image", entry["path"], fp.add_image(db, img, entry.get("label", "known-fake"), entry.get("source", ""))))
                elif entry.get("kind") == "text":
                    added.append(("text", entry["text"][:40] + "…", add_reported_text(db, entry["text"], entry.get("label", "scam"))))
        elif not args.demo:
            print(f"No manifest at {manifest}. Add one, or run with --demo.")
    for kind, name, record_id in added:
        print(f"  {kind:5s} {record_id}  {name}")
    print(f"Added {len(added)}.")


if __name__ == "__main__":
    main()
