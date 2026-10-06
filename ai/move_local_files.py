"""Move your local AI files into ai/, once, after the git pull that created ai/.

git moves the files it tracks. Files that only exist on your computer stay in the
old places: trained models, learning data, test batches, eval/external/sms.tsv,
logs, reports, backups. This script moves those into the same place under ai/.

    python ai/move_local_files.py --dry-run    # only show what would move
    python ai/move_local_files.py              # move them

It never overwrites: if a file already exists in ai/, both are kept and it is
listed at the end. It deletes nothing, except empty folders left behind, and
Python's own cache folders (__pycache__) only if you add --remove-caches.
"""
import argparse
import shutil
from pathlib import Path

AI = Path(__file__).resolve().parent
ROOT = AI.parent

# Old place (from the repository root) -> the same path under ai/
OLD_PLACES = ["models", "src", "training", "routine", "eval", "reports", "runs", "backup", "scratch", "logs",
              "data/anomaly", "data/continuity", "data/precedent", "data/rounds", "data/similarity",
              "data/detection", "data/learning", "data/scam_reports.json"]


def files_under(path: Path):
    return [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="only show what would move")
    ap.add_argument("--remove-caches", action="store_true", help="also delete old __pycache__ folders")
    args = ap.parse_args(argv)

    moved, kept_both = [], []
    for name in OLD_PLACES:
        old = ROOT / name
        if not old.exists():
            continue
        for src in files_under(old):
            rel = src.relative_to(ROOT)
            if "__pycache__" in rel.parts:
                continue  # Python rebuilds these; see --remove-caches
            dst = AI / rel
            if dst.exists():
                kept_both.append(rel)
                continue
            moved.append(rel)
            if not args.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))

    left = []
    for name in OLD_PLACES:
        old = ROOT / name
        if not old.is_dir():
            continue
        if args.remove_caches and not args.dry_run:
            for cache in sorted(old.rglob("__pycache__"), reverse=True):
                shutil.rmtree(cache)
        if not args.dry_run:
            for folder in sorted((p for p in old.rglob("*") if p.is_dir()), reverse=True):
                if not any(folder.iterdir()):
                    folder.rmdir()  # empty
            if not any(old.iterdir()):
                old.rmdir()
        if old.exists():
            left.append(name)

    verb = "Would move" if args.dry_run else "Moved"
    print(f"{verb} {len(moved)} file(s) into ai/.")
    for rel in moved[:40]:
        print(f"  {rel}  ->  ai/{rel}")
    if len(moved) > 40:
        print(f"  ... and {len(moved) - 40} more")
    if kept_both:
        print(f"\n{len(kept_both)} file(s) exist in both places, so both were kept. Compare them, then delete the "
              "old one yourself:")
        for rel in kept_both:
            print(f"  {rel}   (and ai/{rel})")
    if left and not args.dry_run:
        print("\nStill there (cache files or the files listed above): " + ", ".join(left)
              + ".\nOnly Python cache files? Run again with --remove-caches.")
    if moved and not args.dry_run:
        print("\nNext: python ai/install_schedule.py   (points both 2-hour routines at their new place)")


if __name__ == "__main__":
    main()
