"""Steps 6-7: the scheduled accuracy routine. A plain Python script; it never calls Claude.

    python run_cycle.py

Each run:
  1. takes the NEXT UNUSED numbered test batch for video and for text
  2. scores it with the current trained detector (no training, no tuning)
  3. computes accuracy, precision, recall, F1, ROC-AUC and the confusion matrix
  4. marks the batch as used, so it is never scored again
  5. prints a two-line summary, appends to reports/history.csv and rewrites reports/latest.md

When a detector's batches run out it logs a warning and stops for that
detector instead of reusing old ones. A detector that isn't trained yet is
skipped without using up a batch. A lock file stops two runs overlapping.
Logs go to logs/run_cycle.log.
"""
import csv
import hashlib
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# All paths come from detection_common (relative to this folder), so it doesn't
# matter which folder Task Scheduler or cron starts the script from.
from detection_common import (KINDS, LABELS, LOGS_DIR, REPORTS_DIR, load_config, load_manifest, mark_batch_used,
                              metrics, read_csv, resolve, sha256_file, split_dir, used_batches)

log = logging.getLogger("run_cycle")
HISTORY = REPORTS_DIR / "history.csv"
LATEST = REPORTS_DIR / "latest.md"
HISTORY_FIELDS = ["run_at", "detector", "batch", "n", "accuracy", "precision", "recall", "f1", "roc_auc",
                  "tn", "fp", "fn", "tp", "model", "note"]


# ---------------------------------------------------------------- lock
class RunLock:
    """A lock file that exists while a run is going. If it is older than
    LOCK_STALE_HOURS the earlier run must have crashed, so it is taken over."""

    def __init__(self, path: Path, stale_hours: float):
        self.path, self.stale_hours, self.held = path, stale_hours, False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and time.time() - self.path.stat().st_mtime > self.stale_hours * 3600:
            log.warning("Removing a stale lock file from a run that did not finish: %s", self.path)
            self.path.unlink(missing_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # fails if it already exists
        except FileExistsError:
            return self
        with os.fdopen(fd, "w") as f:
            f.write(f"pid {os.getpid()} started {datetime.now().isoformat(timespec='seconds')}\n")
        self.held = True
        return self

    def __exit__(self, *exc):
        if self.held:
            self.path.unlink(missing_ok=True)


# ---------------------------------------------------------------- scoring
def model_fingerprint(path: Path) -> str:
    """Short hash of the model file(s), so the history shows when the model changed."""
    if not path.exists():
        return "missing"
    files = sorted(p for p in path.iterdir() if p.suffix in (".safetensors", ".bin")) if path.is_dir() else [path]
    h = hashlib.sha256("".join(sha256_file(p) for p in files).encode())
    return h.hexdigest()[:12]


def score_video(rows, cfg) -> tuple[list[int], list[float], str]:
    from video_detector import VideoDetector
    detector = VideoDetector(cfg["video"]["model_path"])
    labels, scores, no_face, failed = [], [], 0, 0
    for row in rows:
        try:
            result = detector.score_video(row["path"])
        except Exception as exc:  # an unreadable file is reported, not guessed
            failed += 1
            log.error("Could not score %s: %s", row["path"], exc)
            continue
        labels.append(row["label"])
        scores.append(result["score"])
        no_face += not result["faces_found"]
    notes = []
    if no_face:
        notes.append(f"{no_face} video(s) had no detectable face (frame centres used)")
    if failed:
        notes.append(f"{failed} video(s) could not be read and are left out")
    return labels, scores, "; ".join(notes)


def score_text(rows, cfg) -> tuple[list[int], list[float], str]:
    from text_detector import TextDetector
    detector = TextDetector(cfg["text"]["model_dir"])
    return [r["label"] for r in rows], detector.score([r["text"] for r in rows]).tolist(), ""


def run_detector(kind: str, cfg: dict) -> dict:
    """Score the next unused batch for one detector. Returns a result dict with
    status 'ok', or 'skipped' plus a reason."""
    manifest = load_manifest(kind)
    if manifest is None:
        return {"kind": kind, "status": "skipped", "reason": f"no test batches yet (run prepare_data.py {kind})"}
    model_path = resolve(cfg[kind]["model_path"] if kind == "video" else cfg[kind]["model_dir"])
    if not model_path.exists():
        return {"kind": kind, "status": "skipped", "reason": f"not trained yet ({model_path.name} missing)"}
    used = set(used_batches(kind))
    remaining = [b for b in manifest["batches"] if b["name"] not in used]
    if not remaining:
        log.warning("All %d %s test batches have been used. Stopping for %s: old batches are never reused. "
                    "Prepare a NEW held-out dataset to keep measuring.", len(manifest["batches"]), kind, kind)
        return {"kind": kind, "status": "skipped", "reason": "no unused test batches left (never reused)"}
    batch = remaining[0]
    path = split_dir(kind) / batch["file"]
    if sha256_file(path) != batch["sha256"]:  # frozen test data must not change after the split
        log.error("%s changed after the split (hash mismatch). Not using it.", path)
        return {"kind": kind, "status": "skipped", "reason": f"{batch['name']} was modified after the split"}

    rows = read_csv(path)
    labels, scores, note = (score_video if kind == "video" else score_text)(rows, cfg)
    if not labels:
        return {"kind": kind, "status": "skipped", "reason": f"nothing in {batch['name']} could be scored"}
    m = metrics(labels, scores)
    mark_batch_used(kind, batch["name"])  # only after a successful score: this batch is now spent
    return {"kind": kind, "status": "ok", "batch": batch["name"], "metrics": m, "note": note,
            "model": model_fingerprint(model_path), "remaining": len(remaining) - 1}


# ---------------------------------------------------------------- reporting
def summary_line(results: list[dict]) -> str:
    parts = []
    for r in results:
        name = r["kind"].capitalize()
        if r["status"] == "ok":
            m = r["metrics"]
            parts.append(f"{name}: {m['accuracy']:.1%} accuracy, F1 {m['f1']:.2f} (n={m['n']}).")
        else:
            parts.append(f"{name}: skipped, {r['reason']}.")
    return " ".join(parts)


def append_history(results: list[dict], run_at: str):
    new = not HISTORY.exists()
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        if new:
            w.writeheader()
        for r in results:
            if r["status"] != "ok":
                continue
            m = r["metrics"]
            w.writerow({"run_at": run_at, "detector": r["kind"], "batch": r["batch"], "n": m["n"],
                        **{k: (f"{m[k]:.4f}" if m[k] is not None else "") for k in
                           ("accuracy", "precision", "recall", "f1", "roc_auc")},
                        **{k: m[k] for k in ("tn", "fp", "fn", "tp")}, "model": r["model"], "note": r["note"]})


def write_latest(results: list[dict], run_at: str, line: str):
    out = [f"# Latest accuracy run: {run_at}", "", line, ""]
    for r in results:
        out.append(f"## {r['kind'].capitalize()} detector")
        if r["status"] != "ok":
            out += [f"Skipped: {r['reason']}.", ""]
            continue
        m, (neg, pos) = r["metrics"], LABELS[r["kind"]]
        auc = "n/a (batch has one class only)" if m["roc_auc"] is None else f"{m['roc_auc']:.3f}"
        out += [f"Batch `{r['batch']}` (n={m['n']}, used once, {r['remaining']} unused batches left), "
                f"model `{r['model']}`.", "",
                "| Accuracy | Precision | Recall | F1 | ROC-AUC |", "|---|---|---|---|---|",
                f"| {m['accuracy']:.1%} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {auc} |", "",
                f"Confusion matrix (rows = truth, columns = detector says; positive = {pos}):", "",
                f"| | says {neg} | says {pos} |", "|---|---|---|",
                f"| truly {neg} | {m['tn']} | {m['fp']} |", f"| truly {pos} | {m['fn']} | {m['tp']} |", ""]
        if r["note"]:
            out += [f"Note: {r['note']}.", ""]
    out += ["These numbers describe one small held-out batch of the prepared dataset, scored once. They are not "
            "real-world accuracy: real videos and messages differ from any public dataset. Look at the trend in "
            "`python show_report.py`, not at one run.", ""]
    LATEST.parent.mkdir(parents=True, exist_ok=True)
    LATEST.write_text("\n".join(out), encoding="utf-8")


def setup_logging():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    # Under pythonw (Task Scheduler) there is no console: sys.stdout/stderr are None and any
    # library progress bar would crash the run. Send them to a file instead.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(LOGS_DIR / "run_cycle.stderr.log", "a", encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(LOGS_DIR / "run_cycle.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    log.handlers[:] = [file_handler]
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    log.addHandler(console)
    log.setLevel(logging.INFO)


def main(argv=None) -> list[dict]:
    setup_logging()
    cfg = load_config()
    with RunLock(LOGS_DIR / "run_cycle.lock", cfg.get("LOCK_STALE_HOURS", 6)) as lock:
        if not lock.held:
            log.warning("Another run is still going (lock file %s). Skipping this run.", lock.path)
            return []
        log.info("Run started")
        results = []
        for kind in KINDS:
            try:
                results.append(run_detector(kind, cfg))
            except Exception:
                log.exception("%s detector failed", kind)  # one failing detector doesn't stop the other
                results.append({"kind": kind, "status": "skipped", "reason": "error, see logs/run_cycle.log"})
        run_at = datetime.now().isoformat(timespec="seconds")
        line = summary_line(results)
        append_history(results, run_at)
        write_latest(results, run_at, line)
        log.info(line)
        return results


if __name__ == "__main__":
    main()
