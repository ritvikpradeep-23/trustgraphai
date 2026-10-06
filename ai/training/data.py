"""Load the evaluation dataset for training, with the data rules built in.

  corpus split  grow the similarity examples, fit vectorizers, train models
  dev split     tune settings, set cut-offs, compare and choose
  test split    NEVER read here. Only training/final_test.py scores it, once
                per final candidate, after checking the manifest hash.

All of this data is synthetic (written by the generator in eval/).
"""
import hashlib
import json
import re

import numpy as np

from eval.generate import load_split
from eval.leakage import DATA

TRAIN_SPLITS = ("corpus", "dev")
FIELDS = ("id", "text", "label", "category", "split", "template_family", "channel", "language",
          "evasion_type", "novelty", "source")
SHORTCUT_LIMIT = 0.85  # a group that is more than 85% one label is a shortcut risk


def load(split: str, data_dir=DATA) -> list[dict]:
    if split not in TRAIN_SPLITS:
        raise ValueError(f"training code never reads the '{split}' split; "
                         "only training/final_test.py scores the frozen test set")
    return load_split(data_dir / f"{split}.jsonl")


def data_hash(rows: list[dict]) -> str:
    """SHA-256 of the rows a model was trained on, written into each bundle's manifest."""
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: r["id"]):
        h.update(json.dumps(r, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()


def labels(rows: list[dict]) -> np.ndarray:
    return np.array([r["label"] == "scam" for r in rows], dtype=int)


def group_folds(rows: list[dict], k: int = 5, seed: int = 0) -> list[tuple[np.ndarray, np.ndarray]]:
    """K folds where every template family stays on one side, so a model is
    never scored on a near-copy of something it trained on. Families are
    shuffled with a fixed seed, then dealt round-robin within each label so
    every fold has both scams and honest messages."""
    rng = np.random.default_rng(seed)
    fold_of = {}
    for label in ("scam", "legit"):
        fams = sorted({r["template_family"] for r in rows if r["label"] == label})
        rng.shuffle(fams)
        fold_of.update({f: i % k for i, f in enumerate(fams)})
    fold = np.array([fold_of[r["template_family"]] for r in rows])
    return [(np.where(fold != i)[0], np.where(fold == i)[0]) for i in range(k)]


# ------------------------------------------------------------ shortcut checks
def length_bucket(text: str) -> str:
    n = len(text.split())
    return "short (<15 words)" if n < 15 else "medium (15-29)" if n < 30 else "long (30+)"


# Formatting habits of the generator that could tell the labels apart
# without saying anything about scams.
_LINK = re.compile(r"(https?|hxxp)://\S+|\b[\w-]+(\[\.\]|\.| dot )(example|test|invalid)\S*|\[LINK\]", re.I)
_SCAM_STYLE_LINK = re.compile(r"\.test\b|\.invalid\b|sh\.example|[a-z]+-[a-z]+(\.|\[\.\]| dot )example\.com", re.I)


def link_kind(text: str) -> str:
    if "[LINK]" in text:
        return "[LINK] placeholder"
    if not _LINK.search(text):
        return "no link"
    return "reserved-domain, scam style" if _SCAM_STYLE_LINK.search(text) else "reserved-domain, other"


ARTIFACTS = {
    "length": lambda r: length_bucket(r["text"]),
    "link": lambda r: link_kind(r["text"]),
    "has [PHONE]": lambda r: "yes" if "[PHONE]" in r["text"] else "no",
    "has 'Details:' suffix": lambda r: "yes" if "Details:" in r["text"] else "no",
    "has an INV- code": lambda r: "yes" if "INV-" in r["text"] else "no",
}


def balance(rows: list[dict], field: str) -> list[dict]:
    """Share of scams per value of a field (or generator artifact), flagging
    groups that are almost all one label."""
    get = ARTIFACTS.get(field, lambda r: r[field])
    groups = {}
    for r in rows:
        groups.setdefault(get(r), []).append(r["label"] == "scam")
    table = []
    for value, flags in sorted(groups.items()):
        share = float(np.mean(flags))
        table.append({"field": field, "value": value, "n": len(flags), "scam_share": share,
                      "flag": len(flags) >= 10 and max(share, 1 - share) > SHORTCUT_LIMIT})
    return table


# ------------------------------------------------------------ deduplication
def dedupe(rows: list[dict], threshold: float = 0.9) -> tuple[list[dict], list[dict]]:
    """Keep a message only if it isn't a near-copy (word TF-IDF cosine above
    the threshold) of one already kept with the same label."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    kept, dropped = [], []
    for label in ("scam", "legit"):
        group = [r for r in rows if r["label"] == label]
        if not group:
            continue
        texts = [r["text"] for r in group]
        vec = TfidfVectorizer(ngram_range=(1, 1), sublinear_tf=True).fit(texts)
        sims = cosine_similarity(vec.transform(texts))
        keep_idx = []
        for i in range(len(group)):
            if keep_idx and sims[i, keep_idx].max() > threshold:
                dropped.append(group[i])
            else:
                keep_idx.append(i)
        kept += [group[i] for i in keep_idx]
    return kept, dropped


def held_out_texts() -> list[str]:
    """Dev and test message texts, ONLY to drop training examples that are
    near-copies of a held-out message (the same leakage filter the
    evaluation used). Nothing is scored or tuned on these here."""
    return [r["text"] for split in ("dev", "test") for r in load_split(DATA / f"{split}.jsonl")]
