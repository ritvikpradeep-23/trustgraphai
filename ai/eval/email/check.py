"""How does the scam engine do on real scam and honest EMAILS? (real data, public corpora)

    python scripts/import_email_datasets.py         # once: builds the sets in eval/external/email/
    python eval/email/check.py                       # design set: numbers + misses and false alarms
    python eval/email/check.py --set holdout         # held-out set: numbers only
    python eval/email/check.py --model-dir models/candidate/learn_<time>

Same text-only scoring and cut-offs as eval/emotional/check.py: Caution / High re-set on the
development honest messages, plus the website's fixed cut-offs from risk_bands.json.
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AI = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(AI), str(AI / "src")]

from eval import metrics  # noqa: E402
from eval.emotional.check import engine_scores, rules_tag  # noqa: E402
from routine import core  # noqa: E402
from trustgraph.similarity import detector as sim  # noqa: E402

SETS = AI / "eval" / "external" / "email"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="design", choices=["design", "holdout"])
    ap.add_argument("--model-dir", help="candidate bundle (default: the live models/ folder)")
    ap.add_argument("--show", type=int, default=25, help="misses / false alarms to print (design set only)")
    args = ap.parse_args(argv)
    os.chdir(AI)
    sys.stdout.reconfigure(errors="replace")
    model_dir = Path(args.model_dir or "models")
    index = sim.build_index(*sim.load_corpus(str(model_dir / "similarity_corpus.json")))
    dev = core.dev_rows()
    dev_s = engine_scores(index, dev, "email_dev")
    bands = metrics.calibrate(dev_s[np.array([r["label"] != "scam" for r in dev])])
    live = json.loads((model_dir / "risk_bands.json").read_text())

    rows = [json.loads(line) for line in open(SETS / f"{args.set}.jsonl", encoding="utf-8")]
    s = engine_scores(index, rows, f"email_{args.set}")
    scam = np.array([r["label"] == "scam" for r in rows])
    print(f"Rules {rules_tag()}  corpus {model_dir}  ({args.set}: {scam.sum()} scam / {(~scam).sum()} honest emails, real data)")
    for name, c, h in (("dev cut-offs", bands["caution"], bands["high"]), ("site cut-offs", live["caution"], live["high"])):
        caution, high = metrics.hits(s, c), metrics.hits(s, h)
        print(f"{name:13s} (Caution {c:.3f}, High {h:.3f}): scams caught {caution[scam].mean():.1%} / High {high[scam].mean():.1%}; "
              f"honest flagged {caution[~scam].mean():.1%} / High {high[~scam].mean():.1%}")
        groups = defaultdict(list)
        for r, hit in zip(rows, caution):
            groups[r["group"]].append(bool(hit))
        print("   " + ", ".join(f"{g} {sum(v)}/{len(v)}" for g, v in sorted(groups.items())))

    if args.set == "design":  # the held-out set's messages are never shown
        caution = metrics.hits(s, live["caution"])
        shown = 0
        for r, sc, c in zip(rows, s, caution):
            if (r["label"] == "scam") != bool(c) and shown < args.show:
                shown += 1
                expl = sim.similarity_score({"message_text": r["text"]}).explanation
                print(f"  {'MISS ' if r['label'] == 'scam' else 'FALSE'} {sc:.2f} [{r['group']}] {r['text'][:110]!r}\n        -> {expl}")


if __name__ == "__main__":
    main()
