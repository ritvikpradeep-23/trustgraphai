"""Fingerprint images / video frames and look them up in the database."""
from PIL import Image
from sqlalchemy.orm import Session

from app.fingerprint import config, store
from app.fingerprint.hashing import dhash, phash


def check_image(db: Session, img: Image.Image) -> dict:
    return store.lookup(db, "image", phash(img), config.IMAGE_THRESHOLD, dhash(img), config.IMAGE_THRESHOLD)


def check_frames(db: Session, frames: list[Image.Image]) -> dict:
    """Best match over all frames, and how many frames matched anything."""
    results = [check_image(db, f) for f in frames]
    hits = [r for r in results if r["db_match"]]
    best = max(hits, key=lambda r: r["similarity"]) if hits else dict(store.NO_MATCH)
    return {**best, "frames_checked": len(frames), "frames_matched": len(hits)}


def add_image(db: Session, img: Image.Image, label: str, source: str = "") -> str:
    return store.add(db, "image", phash(img), label, source, hash2=dhash(img))
