"""Shared helpers for the deepfake-video and AI-text detectors and the routine.

Kept in one small file so every script reads the config, the splits and the
metrics the same way:
  load_config()   reads detection_config.json and checks INTERVAL_HOURS
  group_split()   train / validation / test-pool split that keeps groups together
  save_splits()   writes the split files plus a manifest of SHA-256 hashes
  metrics()       accuracy, precision, recall, F1, ROC-AUC, confusion matrix
"""
import csv
import hashlib
import json
import os
import random
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "detection_config.json"
SPLITS_DIR = ROOT / "data" / "detection" / "splits"   # one sub-folder per detector: video/, text/
REPORTS_DIR = ROOT / "reports"
LOGS_DIR = ROOT / "logs"
KINDS = ("video", "text")
LABELS = {"video": ("real", "fake"), "text": ("human", "AI")}  # label 0, label 1


# ---------------------------------------------------------------- config
def load_config(path: Path = CONFIG_PATH) -> dict:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    cfg["INTERVAL_HOURS"] = check_interval(cfg.get("INTERVAL_HOURS", 2))
    return cfg


def check_interval(value) -> int:
    """Whole hours from 1 to 23. Below 1 is rejected (as asked). Whole hours
    because both cron and Task Scheduler repeat in whole hours; 24+ would be
    'daily', which needs a different schedule type."""
    try:
        hours = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"INTERVAL_HOURS must be a number, got {value!r}") from None
    if hours < 1:
        raise ValueError(f"INTERVAL_HOURS must be at least 1, got {value}")
    if hours != int(hours) or hours > 23:
        raise ValueError(f"INTERVAL_HOURS must be a whole number of hours from 1 to 23, got {value}")
    return int(hours)


def resolve(path: str) -> Path:
    """Config paths are relative to the project folder, wherever the script is started from."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def best_device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


# ---------------------------------------------------------------- files
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict], fields: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["label"] = int(r["label"])
    return rows


def write_json_atomic(path: Path, data):
    """Write to a temp file then rename, so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# ---------------------------------------------------------------- splits
def group_split(rows: list[dict], fractions: dict, seed: int):
    """Split by GROUP, not by row. A group is e.g. one person's face (video) or
    one question with its human and AI answers (text). Keeping a group on one
    side stops the test pool from containing near-copies of training data."""
    groups = sorted({r["group"] for r in rows})
    random.Random(seed).shuffle(groups)
    n_train = round(len(groups) * fractions["train"])
    n_val = round(len(groups) * fractions["val"])
    side = {g: "train" for g in groups[:n_train]}
    side.update({g: "val" for g in groups[n_train:n_train + n_val]})
    side.update({g: "test" for g in groups[n_train + n_val:]})
    out = {"train": [], "val": [], "test": []}
    for r in rows:
        out[side[r["group"]]].append(r)
    return out["train"], out["val"], out["test"]


def make_batches(test_rows: list[dict], batch_size: int, seed: int) -> list[list[dict]]:
    """Cut the test pool into numbered batches, fixed now, before any testing.
    Rows are shuffled once so every batch has a similar real/fake mix; a last
    batch smaller than half the size is merged into the one before it."""
    rows = list(test_rows)
    random.Random(seed + 1).shuffle(rows)
    batches = [rows[i:i + batch_size] for i in range(0, len(rows), batch_size)]
    if len(batches) > 1 and len(batches[-1]) < batch_size / 2:
        batches[-2].extend(batches.pop())
    return batches


def split_dir(kind: str) -> Path:
    return SPLITS_DIR / kind


def used_batches(kind: str) -> list[str]:
    path = split_dir(kind) / "used_batches.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def mark_batch_used(kind: str, name: str):
    write_json_atomic(split_dir(kind) / "used_batches.json", used_batches(kind) + [name])


def save_splits(kind: str, train, val, batches, fields: list[str], source: str, force: bool = False):
    """Write train.csv, val.csv, test_batches/batch_001.csv ... and manifest.json.

    Refuses to replace splits whose test batches were already used: a new split
    could move already-tested items into training, and the routine's promise
    that each batch is used once would no longer mean anything."""
    folder = split_dir(kind)
    if (folder / "manifest.json").exists():
        if used_batches(kind):
            raise SystemExit(f"{kind} splits already exist and {len(used_batches(kind))} test batch(es) were used. "
                             f"Not replacing them. Move {folder} somewhere else yourself if you really want new splits.")
        if not force:
            raise SystemExit(f"{kind} splits already exist in {folder}. Use --force to replace them "
                             "(allowed only because no test batch has been used yet).")
    write_csv(folder / "train.csv", train, fields)
    write_csv(folder / "val.csv", val, fields)
    batch_dir = folder / "test_batches"
    batch_dir.mkdir(parents=True, exist_ok=True)
    for old in batch_dir.glob("batch_*.csv"):
        old.unlink()  # only reached when no batch was used (checked above)
    entries = []
    for i, batch in enumerate(batches, 1):
        path = batch_dir / f"batch_{i:03d}.csv"
        write_csv(path, batch, fields)
        entries.append({"name": path.stem, "file": f"test_batches/{path.name}", "n": len(batch),
                        "n_label_1": sum(r["label"] for r in batch), "sha256": sha256_file(path)})
    manifest = {"kind": kind, "source": source, "created": datetime.now().isoformat(timespec="seconds"),
                "n_train": len(train), "n_val": len(val), "n_test": sum(len(b) for b in batches),
                "train_groups": len({r["group"] for r in train}), "batches": entries}
    write_json_atomic(folder / "manifest.json", manifest)
    return manifest


def load_manifest(kind: str) -> dict | None:
    path = split_dir(kind) / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


# ---------------------------------------------------------------- metrics
def metrics(labels, scores, threshold: float = 0.5) -> dict:
    """All numbers for one batch. Label 1 = fake video / AI text, and a score
    at or above the threshold counts as label 1."""
    from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score, recall_score,
                                 roc_auc_score)
    labels = [int(x) for x in labels]
    guesses = [int(s >= threshold) for s in scores]
    tn, fp, fn, tp = confusion_matrix(labels, guesses, labels=[0, 1]).ravel()
    both = len(set(labels)) == 2
    return {"n": len(labels),
            "accuracy": float(accuracy_score(labels, guesses)),
            "precision": float(precision_score(labels, guesses, zero_division=0)),
            "recall": float(recall_score(labels, guesses, zero_division=0)),
            "f1": float(f1_score(labels, guesses, zero_division=0)),
            "roc_auc": float(roc_auc_score(labels, scores)) if both else None,  # needs both classes
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}
