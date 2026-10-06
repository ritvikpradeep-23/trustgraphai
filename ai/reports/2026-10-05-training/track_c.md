# Track C: learned text classifier as a fifth signal (verdict: reject)

> Synthetic data except the real-SMS column. Not real-world accuracy.

**What was built:**
- Logistic regression on normalized text: disguise tricks undone, links/phones/amounts/numbers as markers.
- Features: TF-IDF word 1-2 grams + character 3-5 grams, balanced class weights.
- Trained on the 1,413 corpus-split messages. C=10 was chosen by group-aware 5-fold CV on corpus+dev (ROC-AUC
  0.985 to 0.991 across the grid, nearly flat).
- Platt-scaled on out-of-fold scores.
- Fusion weight 0.3, chosen on dev from 0.3 / 0.5 / 1.0.
- It sits on top of the Track B retry examples (similarity_v3).
- It's the "classifier" signal, appended last, only when `TRUSTGRAPH_CLASSIFIER=1`.

## Dev results (each at its own ~10% / ~1% dev false-alarm cut-offs)

| | Scams caught (Caution) | Honest flagged (High) | ROC-AUC | Real UK SMS honest flagged |
|---|---|---|---|---|
| Engine without classifier (similarity_v3) | 91.1% | 1.0% | 0.963 | 16.7% |
| **Engine + classifier (weight 0.3)** | **93.1%** | 1.0% | 0.975 | **31.1%** |
| Engine + classifier (weight 0.5) | 92.7% | 1.0% | 0.974 | |
| Engine + classifier (weight 1.0) | 88.0% | 1.0% | 0.963 | |
| Classifier alone | 75.4% | 1.0% | 0.925 | 45.8% |
| Baseline: message length + has a link | 50.2% | 1.4% | 0.834 | |

## The three-way test (classifier alone, scams caught at matched ~10% false alarms)

| | Caught |
|---|---|
| (a) Random 5-fold CV on corpus (near-copies on both sides) | **100%** |
| (a2) Group 5-fold CV on corpus (template families held out) | 82.3% |
| (b) Dev (families held out) | 75.4% |
| (c) Leave-one-type-out, retrained from scratch per type, mean of 29 | **66.5%** |

**Plainly:** (a) is far above (c). The classifier has learned a lot of the *style* of the generated messages:
it recognises a template it has seen perfectly, and a scam type it has never seen much less well. Inside the
engine it still helps on new types: leave-one-type-out rises from 75.2% to 82.8%. Trained without the 16 types
and scored on them, the engine goes from 90.3% to 91.9%, and the classifier alone reaches 68.8%.

## Shortcut audit
- **Label balance:** see `phase0.md`. After normalization the disguise tricks no longer give the answer away. Scams
  using each trick are caught at 66-86%, versus 75% for undisguised scams. Honest all-lowercase messages are flagged
  9%, the same as plain honest ones (10%).
- **Strongest terms** (`track_c_coefficients.csv`): toward scam "pay", "now", "send", "transfer", "money", "cards",
  "your card", "account", plus the markers `<link>`, `<phone>`, "within `<number>` hours". Toward honest:
  "has been", "can you", "moved to", "tomorrow", "never", "through the", plus `<number>` and "details `<link>`".
  12 of the top 100 hit the watch list (markers, and "details" from the generator's honest-only "Details: link" habit).
  No channel names, brand names or language markers made the top 50.
- **Retrained without the flagged words** (details, `<link>`, `<phone>`, `<amount>`, `<number>`): classifier alone
  75.4% to 69.9%, engine + classifier 93.1% to 92.2%. It leans on them somewhat, not mostly.
- **Trivial baseline:** the classifier clearly beats length + has-link (ROC-AUC 0.925 vs 0.834).

## Decision

| Rule | Result |
|---|---|
| 1. Dev recall up at least 3 points | **no** (+1.9) |
| 2. Leave-one-type-out not lower | yes (75.2% to 82.8%) |
| 3. High false alarms not higher | yes |
| 4. Tests pass | yes |
| 5. Real-SMS false alarms up at most 2 points | **no** (16.7% to 31.1%) |

**Verdict: reject.** The bundle `models/candidate/classifier_v1/` is kept for reference. It was not scored on the
test set, because only final (adopted) candidates are.

## What this means
1. A model that learns from examples got near-perfect scores on messages like the ones it trained on: a warning sign, not a win.
2. On scam types it never saw, it caught about two thirds; inside the full engine it still helped on new types.
3. But it flagged almost half of real people's ordinary texts, because nothing it learned from looks like casual chat.
4. Adding it barely raised catches on top of the improved wording match, and it doubled real-text false alarms.
5. It needs real honest messages (and real scams) to train on before it's worth switching on.
