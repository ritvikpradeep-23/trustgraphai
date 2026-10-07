# ai-model

TrustGraph: scores an interaction (a call, text or email) for scam risk and explains why.

| Signal | Asks | Status |
|---|---|---|
| Anomaly | Does the call behave oddly? (3am, huge amount, many urgent words) | built |
| Continuity | Have the contact's details changed? (new bank account, lookalike email domain) | built |
| Similarity | Does the message read like a known scam? (gift-card codes, "safe account") | built |
| Precedent | Has this number, account, link or wallet been reported as a scam before? | built (demo report list) |

The signals combine into one risk level: **Low**, **Caution** or **High**.

## Try it in your browser

**Windows:** install [Python 3.12](https://www.python.org/downloads/) (tick "Add python.exe to PATH"), then double-click `start_website.bat`.

**Any system:**

```bash
pip install -r requirements.txt
python ai/run_website.py
```

A page opens at http://127.0.0.1:8000. Pick an example from the menu or type your own, then press **Check risk**. It runs only on your computer.

## Run the checks

```bash
python -m pytest tests/                          # unit tests
PYTHONPATH=src python -m trustgraph.evaluate     # named scenarios + false-alarm rate
PYTHONPATH=src python scratch/similarity_check.py 99   # independent check, any seed
```

---

# TrustGraph backend API (`app/`)

One FastAPI service for the website, the browser extension and future messaging bots. Bots and the
extension only carry messages here (`app/integrations/base.py`). All scam logic lives in
`app/scam_engine`.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env                 # optional: edit thresholds, limits, CORS origins, model path
python scripts/seed_reports.py       # optional: 10 example scam reports for the demo
uvicorn app.main:app --port 8001     # then open http://127.0.0.1:8001/docs
```

The first text request downloads the `all-MiniLM-L6-v2` embedding model (~90 MB, once), so it needs internet.

## Endpoints

| Method | Path | Body | Answer |
|---|---|---|---|
| GET | `/health` | none | `status`, `reports_stored`, `embedding_model_loaded` |
| POST | `/api/text/report` | `{"text": "...", "source": "website"}` | `201 {"id": "...", "status": "stored"}` |
| POST | `/api/text/analyze` | `{"text": "...", "source": "extension"}` | `{"risk_level": "LOW/MEDIUM/HIGH", "top_similarity": 0.91, "similar_reports": 2, "matches": [{"id", "similarity", "source"}]}` |

Every error has the same shape, for example `{"error": "empty_text", "detail": "..."}`:

| Code | Error |
|---|---|
| 413 | `text_too_long` |
| 422 | `invalid_request`, `empty_text` |
| 503 | `embedding_model_unavailable` |

```bash
curl -X POST localhost:8001/api/text/analyze -H "Content-Type: application/json" \
     -d '{"text": "Your bank account is blocked, verify at the link", "source": "website"}'
```

## Privacy

- **`/api/text/analyze` never returns another user's report text.** Only the report id, its similarity and its
  source come back.
- **Analyzed text isn't stored.** Only explicit reports are kept, in `REPORTS_PATH`, which is git-ignored.
- **Logs record ids, lengths and sources, never message text.** Validation errors don't echo the submitted text.
- **Uploaded videos are written to a temporary file and always deleted after analysis**, even when it fails.

## Tests

```bash
python -m pytest tests/test_backend_*.py
```

Most text tests use a small stand-in embedder, so they run offline. One test uses the real model, comparing the
reworded bank-suspension scam with "Dinner at 8?". It is skipped if the model can't be downloaded. The video tests
build their own small MP4s and a tiny TorchScript model.
