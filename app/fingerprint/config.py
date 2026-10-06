"""Fingerprint and media-check limits, from environment variables (all optional)."""
import os


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


IMAGE_THRESHOLD = _int("FINGERPRINT_IMAGE_THRESHOLD", 10)  # max differing bits of 64 (pHash AND dHash)
FULL_SCAN_MAX = _int("FINGERPRINT_FULL_SCAN_MAX", 20000)  # up to this many rows, compare beyond the band index
MEDIA_MAX_BODY = _int("MEDIA_MAX_BODY", 8 * 1024 * 1024)  # one /api/media/check request
MEDIA_MAX_IMAGE_BYTES = _int("MEDIA_MAX_IMAGE_BYTES", 3 * 1024 * 1024)  # one decoded image or frame
MEDIA_MAX_FRAMES = _int("MEDIA_MAX_FRAMES", 16)
