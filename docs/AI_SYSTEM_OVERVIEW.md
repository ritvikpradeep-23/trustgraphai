# TrustGraph AI: what is being built

TrustGraph checks what people receive in chats for three things:

1. **Scam messages**: texts that try to trick you (fake bank alerts, OTP requests, fake jobs…).
2. **Deepfake videos**: videos where a face has been swapped or generated.
3. **AI-written text**: messages written by an AI model instead of a person.

Everything runs **on your own laptop**. No accounts, no API keys, no cloud service; message text never leaves the
computer.

> Status: everything runs as **one local service** (`python run_server.py`, http://127.0.0.1:8000). The scam check
> is connected to the browser extension. The AI-text and deepfake video checks have their own endpoints, and the
> AI-text result is added to the extension's scam answers, but both detectors are **not trained on real data yet**, and
> the extension doesn't show them yet.

---

## 1. The big picture

```
 Browser extension (WhatsApp / Gmail / … pages)          Test page in your browser
        │  HTTP + JSON:  POST /api/score                        │  GET /
        ▼                                                       ▼
 ONE local service:  python run_server.py   →   http://127.0.0.1:8000   (FastAPI, Python)
   ├─ POST /api/score            scam check (4-signal engine in src/trustgraph)
   │                             + "ai_written" once the AI-text model is trained
   ├─ POST /api/text/ai-check    AI-written text? (fine-tuned distilroberta)
   ├─ POST /api/video/analyze    deepfake video (EfficientNet-B0 + your head)
   ├─ POST /api/text/report, /api/text/analyze   similar scam reports (sentence embeddings)
   ├─ GET  /api/accuracy         latest results of the accuracy and learning routines
   ├─ POST /api/feedback         "this is a scam" / "wrongly flagged" → learning inbox
   └─ GET  /health, /docs        what is configured, list of all endpoints

 Stand-alone Python (no server):
   ├─ train_video.py / train_text.py      training
   ├─ run_cycle.py   ← Task Scheduler every 2 hours (accuracy routine)
   └─ learn_cycle.py ← every 2 hours: one fresh dataset per run (new-scam learning routine)
```

**How the pieces talk:** the extension calls the **local service** through an **HTTP API** (JSON in, JSON out). The
service is written in Python and loads the AI as **Python modules**. If it doesn't answer within 3 seconds the
extension uses its built-in rules instead. `python run_website.py` (the older server with only the scam check and the
page) still works; don't run both, they use the same port.

---

## 2. The three detectors

| | Scam check | Deepfake video | AI-written text |
|---|---|---|---|
| **Looks at** | Message text + metadata (sender history, urgency words) | Faces in 16 frames spread over the video | Text only |
| **Model** | 4 signals combined: similarity to scam scripts + red-flag patterns, anomaly model (IsolationForest), continuity, precedent | Google **EfficientNet-B0** (pretrained, frozen) + **your layer** on top (1280 features → 1 score) | **distilroberta-base**, fine-tuned for human vs AI |
| **Output** | Low / Caution / High + score + explanation | Fake score 0–1 per video (average of frame scores) | AI score 0–1 per text |
| **Trained on** | Synthetic scam/legit messages (labelled as synthetic) | Not yet. Plan: Celeb-DF v2 | Not yet. Plan: HC3 |
| **Code** | `src/trustgraph/` | `video_detector.py`, `train_video.py`, `app/deepfake_engine/` | `text_detector.py`, `train_text.py` |
| **Reachable over HTTP** | ✅ `POST /api/score` | ✅ `POST /api/video/analyze` (after training, with `DEEPFAKE_MODE=efficientnet`) | ✅ `POST /api/text/ai-check`, and `ai_written` in `/api/score` (after training) |
| **Shown by the extension** | ✅ yes | ❌ not yet | ❌ not yet (the field arrives; the extension ignores it) |

### Your own model's role (deepfake video)

- Your model is the **head**: one small trained layer (`app/deepfake_engine/combined_model.py`).
- **EfficientNet-B0** is the **backbone**. It turns each face into 1,280 numbers, and the head turns those into a fake
  score. This is **transfer learning**.
- **Stage 1** trains only the head, with EfficientNet frozen. **Stage 2** (optional) also adapts EfficientNet's last
  blocks, at a 100× lower learning rate.
- The API can run `DEEPFAKE_MODE=mine`, `efficientnet` or `both`. `both` averages the two image models.

---

## 3. Separate, not multimodal

Each modality is analysed **on its own**. Nothing combines video and text into one judgement.

- **Video ignores audio:** cloned voices are not checked. It also ignores spoken words, and judges each frame
  separately (not motion over time).
- **The scam check** combines 4 signals, but all of them are about the same message.
- **The routine** reports video and text as two separate scores.

**Possible next step: late fusion.** Run each detector separately, then combine their scores (for example a message
with a video attached). A truly joint model would need a dataset where video, audio and text are labelled together.

---

## 4. Data plan

**Rules for all data:**
- Only public datasets.
- Nothing over 1 GB is downloaded without showing the name, source and size first.

**Video**
- **Celeb-DF v2 (recommended):** you fill in the request form yourself; about 10 GB.
- FaceForensics++ also needs a request form.
- DFDC (Kaggle) is about 470 GB in full; a 400-video sample exists.

**Text**
- **HC3** (`Hello-SimpleAI/HC3`, CC-BY-SA-4.0): human and ChatGPT answers to the same questions. Under 1 GB.

**Split:** 60% train, 10% validation, 30% test pool.
- Data is split **by group**: a question with all its answers, or a person's videos, stays on one side. So the test
  pool never contains near-copies of training data.
- The test pool is cut into **numbered batches** before any training, each with a SHA-256 hash.
- Training only reads train and validation.

---

## 5. The accuracy routine

`run_cycle.py` is a plain Python script. It never trains, never tunes and never calls Claude.

Every `INTERVAL_HOURS` (default 2, set in `detection_config.json`):

1. Takes the **next unused test batch** for video and for text.
2. Scores it with the current models.
3. Computes accuracy, precision, recall, F1, ROC-AUC and the confusion matrix.
4. Marks the batch as **used forever**. When batches run out it warns and stops; old batches are never reused.
5. Prints `Video: 91.3% accuracy, F1 0.90 (n=50). Text: 87.5% accuracy, F1 0.86 (n=200).`
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
   plus scams reported through `POST /api/feedback`, `POST /api/text/report` or `add_examples.py`, and honest
   messages that were wrongly flagged.
2. It first records how many of the new scams the engine **already** caught. That's the live new-scam catch rate.
3. It learns the misses, then runs the same safety gate as the improvement rounds.
4. An accepted version waits in `models/candidate/learn_<time>/` until you promote it (or `AUTO_PROMOTE`).

Chance of catching a brand-new scam type: about **6 in 10 on synthetic data**; unknown in real life, probably lower.
Rewordings are caught far better once a few reports of that scam have been learned. Details:
`docs/NEW_SCAM_LEARNING.md`.

## 6. What the numbers mean, and what they don't

- **They do mean:** how the model did on one batch of the prepared dataset that it never trained on, scored once.
- **Small batches wobble.** In a batch of 50 videos, one video is 2 percentage points. Read the trend, not one run.
- **Runs with the same model only show batch-to-batch variation.** The routine is most useful after retraining:
  did the new model do better on data it has never seen?
- **They are not real-world accuracy:**
  - Public deepfake datasets use older methods.
  - HC3 is 2022 ChatGPT answering questions, not chat messages or newer AI models.
- **The tiny end-to-end test numbers mean nothing.** It used untrained models and generated data, and gave 50%: a
  coin toss.

---

## 7. Run it

```
python -m pip install -r requirements.txt
python run_server.py                          # the one local service, port 8000 (extension uses this)
python check_gpu.py                           # is the GPU usable?
python prepare_data.py text --hc3             # then: video --folder <Celeb-DF folder>
python train_video.py ; python train_text.py
python run_cycle.py ; python show_report.py
python install_schedule.py                    # every 2 hours
python -m pytest -q                           # all tests
```

Details: `docs/DETECTION_ROUTINE.md`. Model setup: `models/README.md`.

---

## 8. What's next

1. **Train on real data** (on your laptop): HC3 and Celeb-DF, then let the routine measure. After training the video
   model, put `DEEPFAKE_MODE=efficientnet` in `.env` so the server uses it.
2. **Extension** (needs your decision, it changes what users see): show the `ai_written` result on verdicts, and a
   "check a video" button that calls `/api/video/analyze`.
3. **Later:** late fusion across modalities, checking audio for cloned voices.
