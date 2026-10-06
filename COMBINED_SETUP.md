# One repository, one upload

Layout:

```text
backend/                 FastAPI source, requirements, launcher
front end/               Complete React/Vite frontend
trustgraph_extension/    Complete browser extension
ai/                      Everything AI: models, scam engine (src/), training, routines (ai/README.md)
data/                    Synthetic scam catalog and separate judge paraphrases
scripts/, tests/         Database seeding and verification
run_server.py           Root launcher forwarding to backend/run_server.py
```

No nested Git repositories are needed. Push from the repository root. Do not initialize another Git repo in backend/front end/extension.

## First setup (Windows)

Use Python 3.12 (the tested runtime, pinned in `.python-version`) and Node.js 22.18+. Create root `.env` from `.env.example`, set your PostgreSQL DSN locally, and never share or commit it.

Run from the root in PowerShell:

```powershell
.\setup_combined.ps1 -SeedDemo
.\.venv\Scripts\python backend/run_server.py
```

This installs the backend including original scam-model dependencies, runs genuine inference self-tests, builds the frontend, and optionally adds the synthetic catalog. `-ScamModel` remains accepted for old commands but is no longer required. Media/deepfake AI stays separate. Alternatively follow the manual commands in `front end/README.md`. Open http://127.0.0.1:8000/signup, create your own account, then Analyze. `/health/scam-model` verifies inference independently of the database, returning HTTP 503 if required assets are missing.

The ZIP/source repo intentionally excludes local .env, .git, node_modules, .venv, build artifacts, logs, and private backups. Reinstall/build on the target machine. No database passwords belong in the frontend or ZIP.

## Extension

In Chrome/Edge extensions, enable Developer mode and load the unpacked `trustgraph_extension/` directory yourself. Its default server is port 8000. If running the preview on 8001, change its Backend URL to http://127.0.0.1:8001 in extension settings.

The latest extension uses `/api/detect` for text, `/api/media/check` for media fingerprints, and `/health/database` for connectivity. `/api/score` remains for older clients. Local rules are the offline/unavailable fallback, not an override of the records-first API's final result. To see extension verdicts in the website, open **Settings → New code** and enter that code in the extension popup ("Have a pairing code?"). Verdict metadata, never message text, then syncs; "Open in workspace" opens the saved result. The dashboard connection-status card was removed, but real pairing/sync is still required. No extension install or browser permission was performed automatically.

## Dataset and honest score variation

1,038 distinct synthetic scam messages are seeded additively in PostgreSQL: 36 original authored examples, 302 clean ScamShield publisher-authored examples, and 700 explicitly TrustGraph-authored template variants. Repeated seeding makes no duplicates; normalized/number-only variants are excluded. These are message examples, not 1,038 independent scam mechanisms or verified incidents. Provenance: `data/SCAMSHIELD_NOTICE.md` and `data/authored_scam_provenance.json`.

Thirteen separate unseeded judge queries paraphrase stored examples, including a partial match. Their similarities vary naturally. Exact normalized copies still correctly score 100% similarity: scores are never randomized or capped for appearance.

The records score is word/sequence similarity, not fraud probability. Recalibration against all 1,038 patterns retained the 71.2% demo threshold on 13 unseeded English scam paraphrases and 16 benign controls, including similar scam warnings. It lies between the nearest benign score (70.1%) and scam score (72.3%). Those calibration inputs are not independent validation and do not validate Hindi/Hinglish accuracy; this is not a production safety threshold. Reproduce with `python scripts/calibrate_demo_threshold.py`.

Every eligible pattern is ranked under Exact (100%), Very strong (90–under 100%), Strong (80–under 90%), Partial (71.2–under 80%), or Below threshold. The tier boundaries are descriptive display bands, not separately validated fraud decisions. Below-threshold comparisons are not detected matches. No known match does not prove safety. Read `docs/DEMO_SCAM_PATTERNS.md` for all full texts and demonstration queries.

```text
.venv\Scripts\python scripts/seed_demo_patterns.py
.venv\Scripts\python scripts/verify_demo_patterns.py http://127.0.0.1:8000
```

Real accounts and account-scoped history are implemented. Records are checked first; a qualifying match skips the model. Otherwise the original four-signal engine supplies the final review score. No new or rejected weights were promoted. Default setup and Vercel packaging now include the baseline CPU engine; only isolated local packaging/inference is verified, not a cloud deployment. The model still misses some scams and can flag legitimate warnings; see `docs/SCAM_MESSAGE_PIPELINE.md` and `docs/VERCEL_DEPLOYMENT.md`.

## Vercel: import the repository root, not the frontend folder

Root `vercel.json` defines one ordinary Vercel project: the Vite site as static files and the FastAPI backend as one Python function (`api/index.py`), with same-origin `/api` routing and SPA deep links. No beta Services feature is needed. See `docs/VERCEL_DEPLOYMENT.md` for required environment settings, deployment protection, and what local tests do/do not prove. No cloud deployment was performed.
