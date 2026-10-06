"""Leakage filter and the frozen test-set manifest.

A test message that is almost a copy of something the engine (or our tuning)
has already seen would make results look better than they are. We drop any
test message whose word TF-IDF cosine similarity to the corpus split, the dev
split, or the engine's own reference corpus is above 0.9.
"""
import hashlib
import json
from datetime import date
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from trustgraph.similarity.corpus import LEGIT_MESSAGES, SCAM_SCRIPTS

THRESHOLD = 0.9
DATA = Path("eval/data")
MANIFEST = DATA / "MANIFEST.json"


def engine_reference_texts() -> list[str]:
    return [t for texts in SCAM_SCRIPTS.values() for t in texts] + list(LEGIT_MESSAGES)


def max_similarity(texts: list[str], reference: list[str]) -> tuple[list[float], list[int]]:
    """For each text, its highest cosine similarity to any reference text, and which one."""
    vec = TfidfVectorizer(ngram_range=(1, 1), sublinear_tf=True).fit(texts + reference)
    sims = cosine_similarity(vec.transform(texts), vec.transform(reference))
    return sims.max(axis=1).tolist(), sims.argmax(axis=1).tolist()


def filter_leaks(candidates: list[dict], reference: list[str], threshold: float = THRESHOLD):
    """Return (kept, removed). Removed rows carry the similarity and the text they matched."""
    if not candidates:
        return [], []
    best, idx = max_similarity([r["text"] for r in candidates], reference)
    kept, removed = [], []
    for r, s, j in zip(candidates, best, idx):
        if s > threshold:
            removed.append({**r, "leak_similarity": round(s, 3), "leak_match": reference[j]})
        else:
            kept.append(r)
    return kept, removed


# Text files are hashed with Windows line endings (\r\n) turned into \n:
# Git on Windows rewrites line endings on checkout, which changes the bytes
# but not the content. Binary files are hashed exactly as they are.
TEXT_SUFFIXES = {".json", ".jsonl", ".md", ".csv", ".txt", ".tsv"}


def _bytes_for_hash(path) -> bytes:
    data = Path(path).read_bytes()
    return data.replace(b"\r\n", b"\n") if Path(path).suffix in TEXT_SUFFIXES else data


def sha256(path) -> str:
    return hashlib.sha256(_bytes_for_hash(path)).hexdigest()


def write_manifest(test_path, seed: int, counts: dict, removed: int, path=MANIFEST):
    manifest = {
        "test_file": str(test_path), "test_sha256": sha256(test_path), "generator_seed": seed,
        "created": date.today().isoformat(), "leakage_threshold": THRESHOLD,
        "removed_by_leakage_filter": removed, "counts": counts,
        "note": "Synthetic, AI-written data. Frozen: never tune anything against this file.",
    }
    Path(path).write_text(json.dumps(manifest, indent=2))
    return manifest


def verify_manifest(path=MANIFEST) -> dict:
    """Raise if the frozen test file has changed since it was frozen."""
    manifest = json.loads(Path(path).read_text())
    actual = sha256(manifest["test_file"])
    if actual != manifest["test_sha256"]:
        raise RuntimeError(f"Frozen test set changed: {manifest['test_file']} hash {actual[:12]}... "
                           f"!= manifest {manifest['test_sha256'][:12]}... Make a new test set instead of editing it.")
    return manifest
