"""Fingerprint a payload and look it up: images, video frames and text."""
from PIL import Image

from app.config import Settings
from app.fingerprint import hashing
from app.fingerprint.store import FingerprintStore

NO_MATCH = {"db_match": False, "similarity": None, "matched_record_id": None}


def check_image(store: FingerprintStore, img: Image.Image, settings: Settings) -> dict:
    return store.lookup("image", hashing.phash(img), settings.fingerprint_image_threshold,
                        hashing.dhash(img), settings.fingerprint_image_threshold)


def check_frames(store: FingerprintStore, frames: list[Image.Image], settings: Settings) -> dict:
    """Best match over all frames, and how many frames matched anything."""
    results = [check_image(store, f, settings) for f in frames]
    hits = [r for r in results if r["db_match"]]
    best = max(hits, key=lambda r: r["similarity"]) if hits else dict(NO_MATCH)
    return {**best, "frames_checked": len(frames), "frames_matched": len(hits)}


def check_text(store: FingerprintStore, text: str, settings: Settings) -> dict:
    h = hashing.simhash(text)
    if h is None:
        return dict(NO_MATCH)
    return store.lookup("text", h, settings.fingerprint_text_threshold)


def add_image(store: FingerprintStore, img: Image.Image, label: str, source: str = "") -> str:
    return store.add("image", hashing.phash(img), label, source, hash2=hashing.dhash(img))


def add_text(store: FingerprintStore, text: str, label: str, source: str = "") -> str:
    h = hashing.simhash(text)
    if h is None:
        raise ValueError("text has nothing to fingerprint")
    return store.add("text", h, label, source)
