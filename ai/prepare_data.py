"""Step 3: turn a public dataset into train / validation / numbered test batches.

Text (human vs AI):
    python prepare_data.py text --hc3                    # HC3 from Hugging Face (size checked first)
    python prepare_data.py text --hc3 --limit 600        # small sample for a quick test
    python prepare_data.py text --csv my_texts.csv       # any CSV with columns text,label[,group]

Label 1 means AI-written text; label 0 means human.
The test pool is cut into numbered batches NOW, before anything is trained.
Training never reads them; run_cycle.py uses each batch exactly once.
Nothing over MAX_DOWNLOAD_GB (detection_config.json, default 1 GB) is
downloaded without --allow-large, and the name, source and size are always
printed first.
"""
import argparse
import hashlib
import json

from detection_common import group_split, load_config, make_batches, save_splits

HC3 = {"repo_id": "Hello-SimpleAI/HC3", "filename": "all.jsonl", "license": "CC-BY-SA-4.0"}


# ---------------------------------------------------------------- text
def hc3_rows(max_gb: float, allow_large: bool) -> list[dict]:
    """HC3 (English): questions answered by humans and by ChatGPT. Public, no token needed.
    The dataset is one JSON object per line: question, human_answers[], chatgpt_answers[]."""
    from huggingface_hub import HfApi, hf_hub_download
    found = HfApi().get_paths_info(HC3["repo_id"], [HC3["filename"]], repo_type="dataset")
    if not found:
        raise SystemExit(f"{HC3['filename']} is not in {HC3['repo_id']} any more. Download a human-vs-AI CSV "
                         "yourself and use --csv instead.")
    info = found[0]
    size_gb = info.size / 1e9
    print(f"Dataset: HC3 ({HC3['filename']}), source: huggingface.co/datasets/{HC3['repo_id']}, "
          f"size: {info.size / 1e6:.1f} MB, licence: {HC3['license']}")
    if size_gb > max_gb and not allow_large:
        raise SystemExit(f"That is over {max_gb} GB. Not downloading. Re-run with --allow-large if you agree.")
    path = hf_hub_download(HC3["repo_id"], HC3["filename"], repo_type="dataset")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            # One group per question: its human and AI answers must land on the same side of the split.
            group = "q" + hashlib.sha1(item["question"].encode("utf-8")).hexdigest()[:12]
            for label, key in ((0, "human_answers"), (1, "chatgpt_answers")):
                for answer in item.get(key) or []:
                    if answer and answer.strip():
                        rows.append({"text": answer.strip(), "label": label, "group": group})
    return rows


def csv_rows(path: str) -> list[dict]:
    import csv
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f)):
            rows.append({"text": r["text"], "label": int(r["label"]), "group": r.get("group") or f"row{i}"})
    return rows


def synthetic_text_rows(n: int) -> list[dict]:
    """Made-up sentences for a plumbing test only. The 'AI' ones just use
    different words, so any score on them means nothing."""
    human = ["omw, be there in 10", "lol did u see that", "can't make it tonight sorry", "who's bringing snacks"]
    ai = ["Certainly! Here is a concise overview of the topic.", "As an AI language model, I can help with that.",
          "In summary, there are several key factors to consider.", "I hope this helps clarify the situation."]
    return [{"text": f"{(ai if i % 2 else human)[i % 4]} ({i})", "label": i % 2, "group": f"s{i // 2}"}
            for i in range(n)]


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["text"])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--hc3", action="store_true", help="text: download HC3 from Hugging Face")
    src.add_argument("--csv", help="text: CSV with columns text,label[,group]")
    src.add_argument("--synthetic", type=int, metavar="N", help="N generated examples (plumbing test only)")
    ap.add_argument("--limit", type=int, help="keep only this many groups (a small sample for testing)")
    ap.add_argument("--allow-large", action="store_true", help="allow a download over MAX_DOWNLOAD_GB")
    ap.add_argument("--force", action="store_true", help="replace existing splits (only if no batch was used)")
    args = ap.parse_args(argv)
    cfg = load_config()

    if args.hc3:
        rows, source = hc3_rows(cfg["MAX_DOWNLOAD_GB"], args.allow_large), f"HC3 ({HC3['repo_id']})"
    elif args.csv:
        rows, source = csv_rows(args.csv), f"CSV {args.csv}"
    else:
        rows, source = synthetic_text_rows(args.synthetic), "SYNTHETIC (plumbing test only)"
    fields = ["text", "label", "group"]

    if args.limit:  # a sample of whole groups, so the split still keeps groups together
        import random
        groups = sorted({r["group"] for r in rows})
        keep = set(random.Random(cfg["split"]["seed"]).sample(groups, min(args.limit, len(groups))))
        rows = [r for r in rows if r["group"] in keep]
        source += f", sample of {len(keep)} groups"
    if not rows or len({r["label"] for r in rows}) < 2:
        raise SystemExit("need examples of both labels")

    train, val, test = group_split(rows, cfg["split"], cfg["split"]["seed"])
    batches = make_batches(test, cfg[args.kind]["test_batch_size"], cfg["split"]["seed"])
    if not batches:
        raise SystemExit("the test pool is empty: use more data")
    m = save_splits(args.kind, train, val, batches, fields, source, force=args.force)
    print(f"{args.kind}: {m['n_train']} train, {m['n_val']} validation, {m['n_test']} test in "
          f"{len(batches)} numbered batches ({source}). Groups never cross between sides.")
    return m


if __name__ == "__main__":
    main()
