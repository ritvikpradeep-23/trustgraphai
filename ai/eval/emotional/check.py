"""How do the text models do on emotional-manipulation messages? (synthetic data)

    python eval/emotional/check.py                 # design set: numbers + every miss/false alarm
    python eval/emotional/check.py --set holdout   # held-out set: numbers only
    python eval/emotional/check.py --ai-text       # also run the AI-written-text detector

Scam engine: the same text-only scoring the learning gate uses. Caution and High
cut-offs are re-set on the development honest messages (about 10% / 1% flagged),
so a change can't look better just by flagging more. Plus the real UK SMS
false-alarm check (real data, honest texts only).
"""
import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AI = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(AI), str(AI / "src")]

from eval import metrics  # noqa: E402
from routine import core  # noqa: E402
from training import scoring  # noqa: E402
from trustgraph.similarity import detector as sim  # noqa: E402

HERE = Path(__file__).resolve().parent


def rules_tag() -> str:
    """Short hash of the red-flag rules (scoring.base_signals keys its cache on it too)."""
    return hashlib.sha1(json.dumps(sim.RED_FLAGS).encode()).hexdigest()[:8]


def engine_scores(index, rows, name):
    base = scoring.base_signals(name, rows)
    return scoring.fuse(base, scoring.similarity_scores(index, rows, base["flag_keep"])[1])


def load(name):
    return [json.loads(line) for line in open(HERE / f"{name}.jsonl", encoding="utf-8")]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", default="design", choices=["design", "holdout"])
    ap.add_argument("--model-dir", help="candidate bundle (default: the live models/ folder)")
    ap.add_argument("--ai-text", action="store_true", help="also score with the AI-written-text detector")
    args = ap.parse_args(argv)

    import os
    os.chdir(AI)
    corpus = Path(args.model_dir or "models") / "similarity_corpus.json"
    index = sim.build_index(*sim.load_corpus(str(corpus)))
    dev = core.dev_rows()
    dev_s = engine_scores(index, dev, "emo_dev")
    is_scam = np.array([r["label"] == "scam" for r in dev])
    bands = metrics.calibrate(dev_s[~is_scam])

    rows = load(args.set)
    s = engine_scores(index, rows, f"emo_{args.set}")
    caution = metrics.hits(s, bands["caution"])
    high = metrics.hits(s, bands["high"])
    scam = np.array([r["label"] == "scam" for r in rows])

    sms = scoring.sms_rows()
    sms_legit = [r for r in sms if r["label"] == "legit"]
    sms_fa = float(metrics.hits(engine_scores(index, sms_legit, "emo_sms"), bands["caution"]).mean()) if sms_legit else None

    print(f"Rules {rules_tag()}  corpus {corpus}  (synthetic data except the real-SMS line)")
    print(f"Cut-offs from dev honest messages: Caution {bands['caution']:.3f}, High {bands['high']:.3f}")
    print(f"{args.set}: emotional scams caught at Caution {caution[scam].mean():.1%} ({caution[scam].sum()}/{scam.sum()}), "
          f"at High {high[scam].mean():.1%}")
    print(f"{args.set}: honest emotional messages flagged at Caution {caution[~scam].mean():.1%} "
          f"({caution[~scam].sum()}/{(~scam).sum()}), at High {high[~scam].mean():.1%}")
    # What the website does: the fixed cut-offs in risk_bands.json (set on full interactions with call
    # metadata). With text only, wording alone is capped at MATCH_CAP, so only a red flag reaches Caution.
    live = json.loads((Path(args.model_dir or "models") / "risk_bands.json").read_text())
    lc, lh = metrics.hits(s, live["caution"]), metrics.hits(s, live["high"])
    print(f"{args.set} at the site's cut-offs (Caution {live['caution']:.3f}, High {live['high']:.3f}): scams caught "
          f"{lc[scam].mean():.1%} / High {lh[scam].mean():.1%}; honest flagged {lc[~scam].mean():.1%} / High {lh[~scam].mean():.1%}")
    print(f"dev: scams caught at Caution {metrics.hits(dev_s[is_scam], bands['caution']).mean():.1%}, "
          f"honest at High {metrics.hits(dev_s[~is_scam], bands['high']).mean():.1%}")
    if sms_fa is not None:
        print(f"real UK SMS honest texts flagged at Caution: {sms_fa:.2%} (real data)")

    groups = defaultdict(list)
    for r, c in zip(rows, caution):
        groups[(r["label"], r["group"])].append(bool(c))
    print("\nPer group (share flagged at Caution):")
    for (label, group), v in sorted(groups.items()):
        print(f"  {label:6s} {group:22s} {sum(v)}/{len(v)}")

    if args.set == "design":  # the held-out set's individual messages are never shown
        print("\nMisses and false alarms (with the engine's own explanation):")
        for r, sc, c in zip(rows, s, caution):
            if (r["label"] == "scam") != bool(c):
                expl = sim.similarity_score({"message_text": r["text"]}).explanation
                kind = "MISS " if r["label"] == "scam" else "FALSE"
                print(f"  {kind} {sc:.2f} [{r['group']}] {r['text'][:70]}\n        -> {expl}")

    if args.ai_text:
        from text_detector import TextDetector
        best = sorted(p for p in Path("models/candidate").glob("text_*") if (p / "model.safetensors").exists())[-1]
        ai = TextDetector(str(best)).score([r["text"] for r in rows])
        print(f"\nAI-written-text detector {best.name}: mean 'AI' score, scams {ai[scam].mean():.2f}, "
              f"honest {ai[~scam].mean():.2f}; flagged as AI (>=0.5): {np.mean(ai >= 0.5):.0%} of all messages")


if __name__ == "__main__":
    main()
