# Training summary

> **All training, dev and test data is synthetic** (AI-written by the generator in `eval/`). The only real data is
> the public UCI SMS Spam Collection (4,827 honest UK texts), used **only** as a false-alarm check. No number here
> is real-world accuracy.

Plan and approvals: `PLAN.md`. Data check: `phase0.md`. Details per track: `track_b.md`, `track_c.md`, `track_a.md`.
Every command and seed: `runlog.md`.

## Decision table

| Candidate | What it is | Verdict | Why |
|---|---|---|---|
| `similarity_v2` | Similarity examples + all corpus-split messages | **reject** | Real-SMS false alarms 19.3% to 34.3% |
| `similarity_v3` | Similarity examples + the 10 most varied corpus messages per type + 40 casual honest texts | **adopt with caveats** | All rules pass; dev recall 16 points above leave-one-type-out; test High false alarms 1.6% to 4.0% |
| `classifier_v1` | Learned text classifier as a fifth signal (on top of v3) | **reject** | +1.9 points only; real-SMS false alarms 16.7% to 31.1% |
| `anomaly_v2` | Anomaly model retrained on 20,000 normal rows incl. honest odd cases | **reject** | Demo: 17/18 scams, 5/6 honest kept Low (was 18/18, 6/6) |
| *(not packaged)* current examples + the 40 casual texts only | Control from Track B | not a candidate | Dev 71.7%, real-SMS false alarms **9.6%** |

Nothing was promoted. `scripts/promote_model.py` exists but was not run.

## Before and after at matched false-alarm rates (dev, text only)

Each row uses its own cut-offs, flagging about 10% (Caution) and 1% (High) of dev honest messages.

| | Scams caught (Caution) | Leave-one-type-out mean (29 types) | Built without 16 types, scored on them | Real UK SMS honest flagged |
|---|---|---|---|---|
| Current engine | 70.6% [66.1, 74.8] | 56.8% | 55.1% | 19.3% |
| + all corpus examples (v2) | 91.4% | 79.1% | 75.7% | 34.3% |
| + capped examples + casual texts (v3) | 91.2% | 75.2% | 75.3% | 16.7% |
| v3 + classifier (weight 0.3) | 93.1% | 82.8% | 91.9%* | 31.1% |
| Current + casual texts only (control) | 71.7% | not run | not run | 9.6% |

\*Engine with v3 examples plus a classifier trained without the 16 types. The v3 examples themselves include those
types, so this mostly measures the classifier.

## One-time test result (frozen test set, sha256 `6fc6fd28…`, verified)

Only the adopted candidate was scored, once. This test set was already viewed in two earlier evaluation reports
(never trained or tuned on).

| | Current engine | similarity_v3 |
|---|---|---|
| Scams caught at Caution | 76.1% [73.3, 79.0] | **91.1%** [89.1, 92.8] |
| Scams caught at High | 50.3% | 69.8% |
| Types the original engine had no examples for (v3 now has examples of them) | 61.1% | 88.4% |
| Hinglish / Manglish scams caught | 84.6% / 79.3% | 93.8% / 91.4% |
| **Honest messages flagged at Caution** | 8.6% | **11.6%** |
| **Honest messages flagged at High** | 1.6% | **4.0%** |
| ROC-AUC | 0.896 | 0.956 |

The test false alarms are higher than on dev (11.6% vs 10%, High 4.0% vs 1%). v3's cut-offs, set on dev, are
in a steep part of the curve, so they don't carry over exactly to new honest messages. It catches more,
**and** flags more honest messages.

## Leave-one-type-out (dev, per type)

`track_b_loco.csv` (similarity examples, current vs v2) and `track_c_loco.csv` (classifier alone, engine with and
without it). Weakest types for the classifier alone, retrained without them:

| Type | Classifier alone | Engine (v3) + classifier | Engine (v3) |
|---|---|---|---|
| Fake CAPTCHA / paste-command | 0% | 100% | 100% |
| Job or advance-fee | 0% | 28% | 50% |
| One-time code request | 15% | 61% | 53% |
| Investment or crypto | 26% | 66% | 66% |
| Parcel / delivery fee | 33% | 66% | 46% |

## Shortcut audit (Track C)
- Phase 0 flagged 12 one-sided groups: disguise tricks only in scams, link styles, "Details:" endings, [PHONE],
  INV- codes, message length.
- Text normalization neutralised the disguise tricks and link styles: disguised scams are caught at 66-86%,
  versus 75% plain.
- Of the classifier's 50 strongest terms each way, 12 are watch-list items (markers and "details"). None are
  channel names, brands or language markers. Retraining without them costs 5 points alone and 1 point in the engine.
- The classifier beats a length + has-link baseline clearly (ROC-AUC 0.925 vs 0.834).
- **But:** 100% on random CV vs 66.5% leave-one-type-out. It learned a lot of the generator's style.

## Biggest remaining misses (dev, similarity_v3, engine's own explanation)

From `remaining_misses_dev.csv`. 40 of 452 dev scams are below Caution.

| Type | Missed | Example (lowest score) | Engine says |
|---|---|---|---|
| Family emergency / new number | 5/13 | "Hiya, this is my new number… can you pay a bill for me today? I'll pay you back Friday." | doesn't resemble known scam scripts (0.13) |
| QR code | 5/13 | "EV charger notice: scan this code to start charging and save your card" | anomaly 0.04, no other signal |
| Electricity disconnection | 5/15 | "Your smart meter subscription expired. Renew at [LINK] or supply will stop." | doesn't resemble known scripts |
| Investment or crypto | 4/15 | "Our quant fund uses artificial intelligence… Minimum deposit Rs 750, returns paid weekly." | no signal |
| Parcel / delivery fee | 3/15 | "your parcel will be destroyed tomorrow unless the storage fee is paid…" | doesn't resemble known scripts; "storage fee" isn't in the fee red-flag list |
| Fake customer care | 3/15 | "download our support app and share the code" | the code red flag needs "code … sent/received" |

**Each cluster is a candidate for the examples or the red flags.** Two are concrete red-flag gaps: "storage fee",
and "share the code" without "sent".

## API changes (all default-off or behaviour-preserving)

| Change | Default behaviour |
|---|---|
| `trustgraph.textnorm.normalize()`, new | Used by the classifier, and by similarity only if a promoted example file says `normalized: true` |
| `similarity.detector.build_index(..., normalized=False)`, `load_corpus()`, `CORPUS_PATH = models/similarity_corpus.json` | No file means the built-in examples, as before |
| `trustgraph.classifier` (signal `"classifier"`), new | Off unless `TRUSTGRAPH_CLASSIFIER=1`; model from `models/classifier.joblib` or `TRUSTGRAPH_CLASSIFIER_MODEL` |
| `pipeline.active_signal_funcs()`; `score_interaction` appends the classifier last when on | Four signals, same order |
| `fusion.DEFAULT_WEIGHTS["classifier"] = 0.5` (replaced by the model's chosen weight) | Unused when off |
| `web/index.html` label for "classifier" | Only shown when on |
| `scripts/promote_model.py` (dry run, `--yes`, `--rollback`), new | Not run |

Places that assume exactly four signals and need a look before the classifier is switched on:
- `tests/test_web.py:42` (exact set of four names)
- `eval/engine.py` (`score_rows`, `refuse` build four signals)
- `eval/run.py` labels ("all four signals")
- teammates' extension popup and the website brief

## Limits
- Every training, dev and test message comes from one generator I wrote. Shared phrasing flatters every
  synthetic number. Leave-one-type-out and the real-SMS check are the honest ones.
- The real-SMS check motivated the Track B retry and gated its choice, so v3's 16.7% is optimistic. The 40 casual
  texts were written after looking at real-SMS false alarms (none copied).
- The frozen test was viewed before (disclosed). Live cut-offs in each bundle's `risk_bands.json` are set on
  synthetic honest messages.
- Time: compute took about 2.5 + 10 min (Track B and retry), 6 min (C) and 5 min (A), all within budget. Nothing hit the 50%-over stop rule.

## How to check
```
python -m pytest tests/                                 # all tests incl. promote/rollback, classifier, data rules
$env:PYTHONPATH="src;."                                  # Windows PowerShell (Linux/Mac: export PYTHONPATH=src:.)
python -m training.phase0                                # data check
python -m training.track_b --retry                       # Track B retry (about 10 min)
python -m training.track_c                               # Track C (about 6 min)
python -m training.track_a                               # Track A (about 5 min)
python scripts/promote_model.py models/candidate/similarity_v3   # dry run: shows the comparison, changes nothing
```
