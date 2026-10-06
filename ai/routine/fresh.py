"""A brand-new synthetic dataset for one learning run (learn_cycle.py).

Used only when you haven't put a dataset of your own in data/learning/datasets/.

    fresh_dataset(seed, reference) -> rows (text, label, scam_type)

Every call uses a new seed, so every dataset is different. To keep the gate
honest it is built ONLY from the improvement-round templates (rounds 03-12):
never from the development rounds 01-02 (used by the gate) or the final-test
rounds 13-14. Any message with word TF-IDF cosine above 0.9 to `reference`
(everything used or learned before) is dropped, the same leakage rule as the
rounds. Synthetic data: fake names, brands, links and [PHONE] placeholders.
"""
import numpy as np

from eval.generate import EVADE
from eval.leakage import filter_leaks
from routine.generate import CHANNEL_P, CHANNELS, IMPROVE, SCAM_TRICKS, families, fill, frame


def fresh_dataset(seed: int, reference: list[str], n_scam: int = 60, n_legit: int = 120) -> list[dict]:
    rng = np.random.default_rng(seed)
    fams = [f for f in families() if f["round"] in IMPROVE]  # never dev or final-test templates
    rows = []
    for label, target in (("scam", n_scam), ("legit", n_legit)):
        mine = [f for f in fams if f["label"] == label]
        cands, seen = [], set()
        for _ in range(target * 3):  # extra, because near-copies are dropped below
            f = mine[int(rng.integers(len(mine)))]
            text = fill(f["text"], f["slots"], rng)
            if label == "scam" and rng.random() < 0.4:   # the evasion tricks scammers use
                text = EVADE[str(rng.choice(SCAM_TRICKS))](text, rng)
            elif rng.random() < 0.12:                     # casual styling on both labels
                text = EVADE[str(rng.choice(["emoji_padding", "casual_lowercase"]))](text, rng)
            text = frame(text, str(rng.choice(CHANNELS, p=CHANNEL_P)), rng)
            if text not in seen:
                seen.add(text)
                cands.append({"text": text, "label": label, "scam_type": f["category"] if label == "scam" else None})
        kept, _ = filter_leaks(cands, reference)
        rows += [kept[i] for i in sorted(rng.permutation(len(kept))[:target])]
    return [rows[i] for i in rng.permutation(len(rows))]
