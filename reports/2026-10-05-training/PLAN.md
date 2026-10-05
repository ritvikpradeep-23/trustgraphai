# Training plan (for approval, nothing built yet)

> All training and test data here is synthetic (AI-written). No result from this work is real-world accuracy.

## Corrections to the prompt's context (checked against the code)

| The prompt says | What the code actually has |
|---|---|
| Precedent is a stub that returns 0 | Precedent is built: it matches numbers, accounts and links against 407 stand-in scam reports (`data/precedent/reports.json`). With text only, it still finds identifiers inside the message. |
| A browser extension sends text only | There's no extension in this repo. The local website and the evaluation send text only, so continuity and anomaly are nearly idle. The track order B, C, A still makes sense. |
| Anomaly uses six numeric features | Six raw fields (`duration_sec, hour_of_day, amount_ratio, contact_freq_24h, urgency_score, new_channel_flag`). The model sees seven, because the hour is split into sin/cos. Trained on 300 normal rows. |
| The live risk_bands.json must not change | It wasn't changed by training. It *was* recalibrated in the two engine bug-fix commits on this branch, the same way as every earlier engine change. Training will never touch it. |

**Two facts that change how results must be read:**

1. **The training pile (corpus split) contains all 29 scam types**, including the 16 the evaluation called "never seen". Once Track B or C trains on it, those types are no longer unseen. Novelty will be measured two ways:
   - **Leave-one-type-out:** retrain from scratch without type X, then test on X. Done for all 29 types.
   - **A second "13 known types only" version of each candidate,** trained without the 16 types and scored on them. This gives a clean answer to "how does it do on scam types it never saw?"
2. **The frozen test set has already been looked at** in two evaluation reports, and the bug fixes came from reading its errors. It has never been trained on or tuned on. See question 2.

## Phase 0: prerequisite check (then stop and report)

All fields the prompt asks for already exist: id, text, label, category, split, template_family, channel, language, evasion_type, novelty, source. The SHA-256 manifest exists. Phase 0 will:

- re-verify all of this with a script
- confirm no template family appears in two splits
- report label balance per language, channel, evasion trick and length bucket. Any group above 85% one label gets flagged for the shortcut audit.

## Data rules

- **Corpus split** (655 scam / 758 honest): grow the similarity examples, fit vectorizers, train the classifier.
- **Dev split** (452 / 1,498): tune settings, set cut-offs (Caution about 10%, High about 1% of honest messages), compare and choose.
- **Test split** (894 / 1,400, frozen): each *final* candidate is scored once, at the end, after the hash check. The script refuses to score the same candidate twice.
- **Real UK SMS** (4,827 honest texts, already on disk): an extra false-alarm check for every candidate. See question 3.
- **Track A** normal data is generated separately and never contains scam messages.

## Track B: grow the similarity examples (about 2 h)

- Add corpus-split scam and honest messages to the reference lists, after removing near-duplicates (similarity above 0.9) and anything near a dev or test message.
- Keep the negation handling and the wording-only cap.
- Report at matched false alarms: dev recall overall, by language, the 13-types-only version on the 16 types, and leave-one-type-out.
- Output: bundle `models/candidate/similarity_v2/`.

## Track C: a learned text classifier as a fifth signal (about 4 h)

**How it's built:**
- Before training, links, phone numbers, amounts and digit runs are replaced with tokens, the same way for both classes.
- Features are word 1-2 grams plus character 3-5 grams. The model is logistic regression with balanced class weights.
- Regularization is tuned with group-aware cross-validation (folds by template family), then probabilities are calibrated.

**How it plugs in:**
- `classifier_score(interaction)` returns a `RiskSignal("classifier", score, "Message: wording like 'gift card', 'send the code'…")`. The explanation names the top contributing words.
- It is off unless `TRUSTGRAPH_CLASSIFIER=1`, and it is added at the end of the signal list.
- Fusion weight is 0.3, 0.5 or 1.0, chosen on dev.

**Shortcut audit:**
- label balance check
- the 50 strongest words in each direction, flagging placeholders ([LINK], example.com), brand names, language markers and greetings/sign-offs, then retraining without the flagged words and reporting the change
- a trivial baseline (message length plus "has a link") that the classifier must clearly beat

**Tested three ways:**
- dev
- template-family holdout
- leave-one-type-out, retraining everything for each type

If leave-one-type-out is much worse, I'll say plainly that the model learned the style of the generated data. There's also a dev comparison of the engine with and without the classifier.

Output: bundle `models/candidate/classifier_v1/`.

## Track A: retrain the anomaly model (optional, about 2 h)

- Generate about 20,000 normal interactions, including honest odd cases (late-night messages, a large one-off payment, a burst of family messages), and retrain on normal data only.
- Injected anomalies come from a separate function.
- Compare with the current model at matched false alarms on normal rows.
- Note: this only matters once something sends hour, frequency and new-sender details.
- Output: bundle `models/candidate/anomaly_v2/`.

## Adoption criteria

The prompt's four rules, compared at matched dev false-alarm rates:
1. Dev recall at Caution rises by at least 3 points.
2. Mean leave-one-type-out recall does not drop.
3. High-band dev false alarms do not rise.
4. All tests pass.

If leave-one-type-out is more than 15 points below dev, the verdict is "adopt with caveats".

**Proposed addition:** (5) false alarms on the real UK SMS must not rise by more than 2 points at the candidate's own cut-offs. It's the only real data we have, and the last fix showed synthetic-only numbers can hide a real-text regression.

## Files

**New:**
- `training/__init__.py`
- `training/data.py`: load splits, field/family/hash checks, group folds. It never loads test.
- `training/phase0.py`
- `training/bundle.py`: writes the bundle (model files, its own risk_bands.json, MODEL_CARD.md with the synthetic-data notice, manifest with training-data hash, date, library versions, seeds).
- `training/track_b.py`, `training/track_c.py`, `training/track_a.py`
- `training/final_test.py`: one-time test scoring per candidate.
- `src/trustgraph/classifier/{__init__,preprocess,detector}.py`
- `scripts/promote_model.py`:
  - prints current vs candidate dev metrics side by side
  - needs `--yes`
  - backs up what it replaces
  - has `--rollback`
  - **I won't run it.**
- `tests/test_training.py`: split integrity, training code never reads test, hash/tamper check, bundle contents, promote and rollback in a temp folder.
- `tests/test_classifier.py`: flag off gives the same four signals as today, flag on adds "classifier" last, token replacement is identical for both classes, explanation lists words, score is between 0 and 1.
- `reports/2026-10-05-training/`: runlog.md (every command and seed), training_summary.md, pitch_summary.md, CSVs.

**Changed (small, default behavior unchanged):**
- `similarity/detector.py`: uses a promoted example list if `models/similarity_corpus.json` exists, otherwise the built-in one.
- `pipeline.py`: appends the classifier when the flag is on.
- `fusion.py`: adds a "classifier" weight. Today an unknown signal name is an error by design.

## Everything that assumes exactly four signals

| Where | What breaks or looks wrong with a fifth |
|---|---|
| `src/trustgraph/fusion.py` `DEFAULT_WEIGHTS` | Unknown signal name raises an error, so "classifier" must be added |
| `src/trustgraph/pipeline.py` `SIGNAL_FUNCS` and docstrings ("all 4 signals") | List is fixed; text says 4 |
| `tests/test_web.py:42` | Asserts the exact set of four names (passes with the flag off, fails with it on) |
| `src/trustgraph/web/index.html` (signal labels, about line 136) | No friendly label for "classifier"; it would show the raw name |
| `eval/engine.py` `score_rows`, `refuse` | Builds the four signals by hand; needs a classifier column to evaluate it |
| `eval/run.py` labels | Says "all four signals fused" |
| Teammates' extension popup / website brief (not in this repo) | Tell them before promoting |

## Risks

- **Learning the generator's style instead of scams.** This is the biggest risk. 1,413 training messages from about 155 template families is small, so the shortcut audit and leave-one-type-out are the real verdict.
- **Two text signals agreeing for the same reason.** The classifier and the wording match read the same text, so noisy-OR can double count. The fusion-weight search at matched false alarms guards this.
- **Cut-offs set on synthetic honest messages.** That's why real-SMS false alarms rose to 19.3%. Question 3 is about fixing it.
- **The test set has been seen.** Question 2.
- **Time.** If any track runs 50% over budget, I stop and report.
