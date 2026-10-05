"""Promote a candidate bundle into models/ as one unit, or roll the last promotion back.

    python scripts/promote_model.py models/candidate/similarity_v2          # dry run: shows the comparison
    python scripts/promote_model.py models/candidate/similarity_v2 --yes    # promote
    python scripts/promote_model.py --rollback                              # undo the last promotion

Before anything changes it prints the bundle's dev metrics next to the current
engine's and its decision row, and it refuses without --yes. Every file it
replaces is first copied to models/backup/<time>/, with a note of which files
didn't exist before, so --rollback restores the exact previous state.
Restart the server afterwards: models are loaded once per process.

All metrics shown come from synthetic data, not real-world accuracy.
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pct(x):
    return "n/a" if x is None else f"{x:.1%}"


def show(manifest: dict):
    m = manifest.get("dev_metrics", {})
    cur = m.get("current_engine", {})
    print(f"Bundle {manifest['name']} (created {manifest['created']}, synthetic training data)")
    print(f"{'dev metric (matched false-alarm rate)':45s} {'current':>10s} {'candidate':>10s}")
    for key, label in (("recall_caution", "scams caught at Caution"), ("fpr_caution", "honest flagged at Caution"),
                       ("fpr_high", "honest flagged at High"), ("loco_mean", "leave-one-type-out recall"),
                       ("real_sms_false_alarms", "real UK SMS honest flagged")):
        if key in m:
            print(f"  {label:43s} {_pct(cur.get(key)):>10s} {_pct(m.get(key)):>10s}")
    print(f"Decision: {m.get('verdict', 'n/a')}")
    if manifest.get("requires"):
        print(f"Requires: {manifest['requires']}")
    for f, info in manifest["files"].items():
        print(f"  {f} -> {info['target']}")


def promote(bundle: Path, root: Path, yes: bool) -> int:
    manifest = json.loads((bundle / "manifest.json").read_text())
    for f, info in manifest["files"].items():
        if _sha(bundle / f) != info["sha256"]:
            print(f"Refusing: {bundle / f} does not match its manifest hash.")
            return 1
    show(manifest)
    if not yes:
        print("\nDry run: nothing changed. Add --yes to promote.")
        return 0

    backup = root / "models" / "backup" / time.strftime("%Y%m%d-%H%M%S")
    backup.mkdir(parents=True)
    record = {"bundle": manifest["name"], "files": {}}
    for f, info in manifest["files"].items():
        target = root / info["target"]
        record["files"][info["target"]] = target.exists()
        if target.exists():
            dest = backup / info["target"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dest)
    (backup / "backup.json").write_text(json.dumps(record, indent=2))

    # Copy everything next to its target first, then swap each in with an atomic
    # rename, so a failure part-way never leaves a half-written file.
    staged = []
    try:
        for f, info in manifest["files"].items():
            target = root / info["target"]
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_name(target.name + ".promoting")
            shutil.copy2(bundle / f, tmp)
            staged.append((tmp, target))
        for tmp, target in staged:
            os.replace(tmp, target)
    except Exception:
        for tmp, _ in staged:
            tmp.unlink(missing_ok=True)
        restore(backup, root)
        raise
    print(f"\nPromoted {manifest['name']}. Backup: {backup}. Restart the server to load it.")
    return 0


def restore(backup: Path, root: Path):
    record = json.loads((backup / "backup.json").read_text())
    for target, existed in record["files"].items():
        if existed:
            shutil.copy2(backup / target, root / target)
        else:
            (root / target).unlink(missing_ok=True)


def rollback(root: Path) -> int:
    backups = sorted((root / "models" / "backup").glob("*/backup.json"))
    if not backups:
        print("Nothing to roll back.")
        return 1
    backup = backups[-1].parent
    record = json.loads(backups[-1].read_text())
    restore(backup, root)
    shutil.rmtree(backup)
    print(f"Rolled back {record['bundle']}: restored the files from {backup.name}. Restart the server.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", nargs="?", help="models/candidate/<name>")
    ap.add_argument("--yes", action="store_true", help="really promote (otherwise a dry run)")
    ap.add_argument("--rollback", action="store_true", help="undo the last promotion")
    ap.add_argument("--root", default=".", help="project folder (default: current folder)")
    args = ap.parse_args(argv)
    root = Path(args.root)
    if args.rollback:
        return rollback(root)
    if not args.bundle:
        ap.error("give a bundle folder or --rollback")
    return promote(Path(args.bundle), root, args.yes)


if __name__ == "__main__":
    sys.exit(main())
