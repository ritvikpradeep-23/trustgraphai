# TrustGraph AI: what is being built

For every function's capabilities, limits and tuning settings, see `docs/CAPABILITIES_AND_LIMITS.md`.

TrustGraph checks what people receive in chats for two things:

1. **Scam messages**: texts that try to trick you (fake bank alerts, OTP requests, fake jobs…). This is the AI that is
   fully working.
2. **AI-written text**: messages written by an AI model instead of a person.

The full model runtime can run **on your own laptop**, without an external model-provider key. The workspace now has real accounts; remote extension checks transmit text transiently to the backend address you configure. The default Vercel runtime uses catalog fallback rather than the trained scam model. See [current integration and limits](ACCOUNT_EXTENSION_INTEGRATION.md).

> Status: the website backend (`python backend/run_server.py`, http://127.0.0.1:8000) has the AI-text engine built
> in (`backend/app/ai/`). It answers once you install `ai/requirements-ai.txt` and train it on your computer; until
> then it says "pending" and never makes up a score. It is **not trained on real data yet**. The original 4-signal scam engine is also connected to `/api/detect` and account Analyze checks when `requirements-scam.txt` is installed. Training routines remain separate.

---

## 1. The big picture

```
 Browser extension / React website ("front end/")
        │  HTTP + JSON
        ▼
 Website backend:  python backend/run_server.py   →   http://127.0.0.1:8000   (FastAPI + PostgreSQL)
   ├─ POST /api/detect, /api/score, /api/reports …   scam matching against PostgreSQL reports (teammate's)
   ├─ POST /api/text/ai-check    AI-written text? (through TrustGraphAI.analyze, backend/app/services/ai_model.py)
   ├─ POST /api/media/check      known-fakes fingerprint match only (no model)
   └─ GET  /health, /docs        status, list of all endpoints
                                         │ only if installed AND trained
                                         ▼
                      backend/app/ai/   text: distilroberta-base fine-tuned (models/text_detector)

 Stand-alone Python (no server, needs requirements-ai.txt):
   ├─ src/trustgraph/                     the 4-signal scam engine (run_website.py demo page)
   ├─ train_text.py                       AI-text training
   ├─ run_cycle.py   ← every 2 hours (accuracy routine)
   └─ learn_cycle.py ← every 2 hours: one fresh dataset per run (new-scam learning routine)
```

**How the pieces talk:** the website and extension call the backend through an **HTTP API** (JSON in, JSON out). The
backend loads the AI as **Python modules**, once, the first time a check needs them. The AI-text packages (PyTorch,
transformers) are optional, in `requirements-ai.txt`, so the hosted Vercel copy stays small: without them, or without
a trained model, the AI-text check answers "pending AI integration; no score was produced".

---

## 2. The two detectors

| | Scam check | AI-written text |
|---|---|---|
| **Looks at** | Message text + metadata (sender history, urgency words) | Text only |
| **Model** | 4 signals combined: similarity to scam scripts + red-flag patterns, anomaly model (IsolationForest), continuity, precedent | **distilroberta-base**, fine-tuned for human vs AI |
| **Output** | Low / Caution / High + score + explanation | AI score 0–1 per text |
| **Trained on** | Synthetic scam/legit messages (labelled as synthetic) | Not yet. Plan: HC3 |
| **Code** | `src/trustgraph/` | `backend/app/ai/text_detector.py`, `text_detector.py`, `train_text.py` |
| **Reachable over HTTP** | ✅ `/api/detect`, `/api/workspace/checks` when the original model/runtime is installed; catalog fallback otherwise | ✅ `POST /api/text/ai-check` (after training) |
| **Shown by the extension** | via the website's own scam matching | ❌ not yet |

---

## 3. Separate checks

The two checks run **on their own**; nothing combines them into one judgement. The scam check combines 4 signals,
but all of them are about the same message. The routine reports the AI-text detector's score on its own.

---

## 4. Data plan

**Rules for all data:**
- Only public datasets.
- Nothing over 1 GB is downloaded without showing the name, source and size first.

**Text**
- **HC3** (`Hello-SimpleAI/HC3`, CC-BY-SA-4.0): human and ChatGPT answers to the same questions. Under 1 GB.

**Split:** 60% train, 10% validation, 30% test pool.
- Data is split **by group**: a question with all its answers stays on one side. So the test
  pool never contains near-copies of training data.
- The test pool is cut into **numbered batches** before any training, each with a SHA-256 hash.
- Training only reads train and validation.

---

## 5. The accuracy routine

`run_cycle.py` is a plain Python script. It never trains, never tunes and never calls Claude.

Every `INTERVAL_HOURS` (default 2, set in `detection_config.json`):

1. Takes the **next unused test batch** for the AI-text detector.
2. Scores it with the current model.
3. Computes accuracy, precision, recall, F1, ROC-AUC and the confusion matrix.
4. Marks the batch as **used forever**. When batches run out it warns and stops; old batches are never reused.
5. Prints `Text: 87.5% accuracy, F1 0.86 (n=200).`
6. Appends to `reports/history.csv`, rewrites `reports/latest.md`, and logs to `logs/`.

**Safety rules:**
- A lock file stops two runs overlapping.
- Missed runs (laptop off) are skipped, not piled up.
- Test batches are hash-checked before use.

**Commands:**
- `python install_schedule.py` installs the schedule (Windows Task Scheduler / cron).
- `--show` checks it exists, and `--remove` deletes it.
- `python show_report.py` prints the latest run and the trend.

---

## 5b. Learning new scams (a fresh dataset every 2 hours)

`learn_cycle.py`, every 2 hours after the last run finished:
1. It takes one fresh dataset it has never used (your files in `data/learning/datasets/`, else a new synthetic one),
   plus scams and wrongly flagged honest messages you add with `add_examples.py`. (Reports made on the website are
   stored in PostgreSQL and are not read by the routine yet.)
2. It first records how many of the new scams the engine **already** caught. That's the live new-scam catch rate.
3. It learns the misses, then runs the same safety gate as the improvement rounds.
4. An accepted version waits in `models/candidate/learn_<time>/` until you promote it (or `AUTO_PROMOTE`).

Chance of catching a brand-new scam type: about **6 in 10 on synthetic data**; unknown in real life, probably lower.
Rewordings are caught far better once a few reports of that scam have been learned. Details:
`docs/NEW_SCAM_LEARNING.md`.

## 6. What the numbers mean, and what they don't

- **They do mean:** how the model did on one batch of the prepared dataset that it never trained on, scored once.
- **Small batches wobble.** In a batch of 200 texts, one text is half a percentage point. Read the trend, not one run.
- **Runs with the same model only show batch-to-batch variation.** The routine is most useful after retraining:
  did the new model do better on data it has never seen?
- **They are not real-world accuracy:**
  - HC3 is 2022 ChatGPT answering questions, not chat messages or newer AI models.
- **The tiny end-to-end test numbers mean nothing.** It used untrained models and generated data, and gave 50%: a
  coin toss.

---

## 7. Run it

Everything AI is in the `ai` folder. Run the AI commands from inside it:

```
cd ai
python -m pip install -r requirements-ai.txt  # website + AI packages
python check_gpu.py                           # is the GPU usable?
python prepare_data.py text --hc3
python train_text.py
python run_cycle.py ; python show_report.py
python install_schedule.py                    # every 2 hours
python -m pytest tests -q                     # AI + routine tests (no database needed)
```

From the repository root (website; PostgreSQL setup is in `TRUSTGRAPH_HANDOFF.md` there):

```
python backend/run_server.py                  # the website backend, port 8000 (needs DATABASE_URL)
python -m pytest -q                           # website + AI tests (needs DATABASE_URL)
```

Details: `docs/DETECTION_ROUTINE.md`. Model setup: `models/README.md` (both inside `ai/`).

---

## 8. What's next

1. **Train on real data** (on your laptop): HC3, then let the routine measure. Restart the backend afterwards so it
   loads the new model.
2. **Extension / website** (needs your decision, it changes what users see): show the AI-text result on verdicts.
3. **Later:** combining the scam and AI-text answers into one verdict, checking audio for cloned voices.
