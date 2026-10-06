"""Perceptual hashes for images and SimHash for text, all 64-bit ints.

phash:   DCT of a 32x32 greyscale copy; bit = low-frequency coefficient above
         the median. Robust to recompression, resizing and small colour shifts.
dhash:   9x8 greyscale copy; bit = pixel brighter than its right neighbour.
         A second, independent view: a match needs BOTH to be close.
simhash: normalised text -> word 1- and 2-grams -> 64-bit SimHash. Changes in
         case, punctuation, spacing and look-alike characters don't move it.
Compare any two with hamming() (number of differing bits, 0-64).
"""
import base64
import binascii
import hashlib
import io
import re
import unicodedata

import numpy as np
from PIL import Image, UnidentifiedImageError

BITS = 64
_ZERO_WIDTH = re.compile("[​‌‍⁠﻿­]")
_INNER_PUNCT = re.compile(r"(?<=\w)[^\w\s]+(?=\w)")
_DATA_URL = re.compile(r"^data:image/[a-z0-9.+-]+;base64,", re.I)


class BadImage(ValueError):
    """The payload isn't a decodable image (or is too big)."""


def decode_image(payload: str, max_bytes: int) -> Image.Image:
    """A data: URL or bare base64 string -> RGB PIL image."""
    if not isinstance(payload, str) or not payload:
        raise BadImage("image payload must be a base64 string or data: URL")
    raw_b64 = _DATA_URL.sub("", payload.strip(), count=1)
    if len(raw_b64) * 3 // 4 > max_bytes:
        raise BadImage(f"image over {max_bytes} bytes")
    try:
        raw = base64.b64decode(raw_b64, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise BadImage("image payload is not valid base64") from exc
    try:
        img = Image.open(io.BytesIO(raw))
        if img.width * img.height > 40_000_000:
            raise BadImage("image has too many pixels")
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise BadImage("image payload is not a readable image") from exc
    return img.convert("RGB")


def _grey(img: Image.Image, w: int, h: int) -> np.ndarray:
    return np.asarray(img.convert("L").resize((w, h), Image.Resampling.LANCZOS), dtype=np.float64)


def _to_int(bits) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | int(bool(bit))
    return value


def _dct_matrix(n: int) -> np.ndarray:
    k = np.arange(n)
    m = np.cos(np.pi * (2 * k[None, :] + 1) * k[:, None] / (2 * n)) * np.sqrt(2 / n)
    m[0] /= np.sqrt(2)
    return m


_DCT32 = _dct_matrix(32)


def phash(img: Image.Image) -> int:
    px = _grey(img, 32, 32)
    low = (_DCT32 @ px @ _DCT32.T)[:8, :8].flatten()
    return _to_int(low > np.median(low[1:]))  # the DC term would dominate the median


def dhash(img: Image.Image) -> int:
    px = _grey(img, 9, 8)
    return _to_int((px[:, 1:] > px[:, :-1]).flatten())


def normalize_text(text: str) -> str:
    """Lowercase, look-alike characters folded (NFKC), zero-width characters,
    punctuation and symbols removed, whitespace collapsed."""
    text = _ZERO_WIDTH.sub("", unicodedata.normalize("NFKC", str(text or ""))).casefold()
    text = _INNER_PUNCT.sub("", text)  # "o.t.p", "don't" -> "otp", "dont"
    text = "".join(" " if unicodedata.category(ch)[0] in "PSZC" else ch for ch in text)
    return " ".join(text.split())


def _h64(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "big")


def simhash(text: str) -> int | None:
    """None when there is no text left after normalisation."""
    words = normalize_text(text).split()
    if not words:
        return None
    features = words + [f"{a} {b}" for a, b in zip(words, words[1:])]
    totals = np.zeros(BITS, dtype=np.int64)
    for token in features:
        h = _h64(token)
        for i in range(BITS):
            totals[i] += 1 if (h >> (BITS - 1 - i)) & 1 else -1
    return _to_int(totals > 0)


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def similarity(distance: int) -> float:
    """0-64 differing bits -> 1.0 (identical) .. 0.0."""
    return round(1 - distance / BITS, 4)


def bands(value: int) -> tuple[int, int, int, int]:
    """The 64-bit hash as four 16-bit bands (indexed columns in the store)."""
    return tuple((value >> shift) & 0xFFFF for shift in (48, 32, 16, 0))


def to_signed(value: int) -> int:
    """SQLite integers are signed 64-bit."""
    return value - (1 << 64) if value >= (1 << 63) else value


def to_unsigned(value: int) -> int:
    return value + (1 << 64) if value < 0 else value
