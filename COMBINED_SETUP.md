# One repository, one upload

Layout:

```text
backend/                 FastAPI source, requirements, launcher
front end/               Complete React/Vite frontend
trustgraph_extension/    Complete browser extension
models/                  Existing legacy model assets (not a new AI engine)
src/, training/, routine/ Existing optional legacy engine/training sources
data/                    Synthetic scam catalog and separate judge paraphrases
scripts/, tests/         Database seeding and verification
run_server.py           Root launcher forwarding to backend/run_server.py
```

No nested Git repositories are needed. Push from the repository root. Do not initialize another Git repo in backend/front end/extension.

## First setup (Windows)

Install Python 3.11+ and Node.js 22.18+. Create root `.env` from `.env.example`, set your PostgreSQL DSN locally, and never share or commit it.

Run from the root in PowerShell:

```powershell
.\setup_combined.ps1 -SeedDemo
.\.venv\Scripts\python backend/run_server.py
```

This installs runtime dependencies, builds the frontend, and optionally adds the synthetic demo patterns. Alternatively follow the manual commands in `front end/README.md`. Open http://127.0.0.1:8000/app/analyze.

The ZIP/source repo intentionally excludes local .env, .git, node_modules, .venv, build artifacts, logs, and private backups. Reinstall/build on the target machine. No database passwords belong in the frontend or ZIP.

## Extension

In Chrome/Edge extensions, enable Developer mode and load the unpacked `trustgraph_extension/` directory yourself. Its default server is port 8000. If running the preview on 8001, change its Backend URL to http://127.0.0.1:8001 in extension settings.

The latest extension uses `/api/detect` for text, `/api/media/check` for media fingerprints, and `/health/database` for connectivity. `/api/score` is also retained for older extension clients. Local rules remain separate from database matching. Account pairing/history sync remains unavailable; extension-local history works separately. No extension install or browser permission was performed automatically.

## Dataset and honest score variation

36 authored synthetic scam examples are seeded additively in PostgreSQL (up from 12); repeated seeding makes no duplicates. Thirteen separate unseeded judge queries paraphrase stored examples, including a partial match. Their similarities vary naturally. Exact normalized copies still correctly score 100% similarity: scores are never randomized or capped for appearance.

The score is word/sequence similarity, not fraud probability or a claim of AI accuracy. The 71.2% demo-calibrated threshold maximizes balanced accuracy on 13 unseeded scam paraphrases and 16 benign controls, including similar scam warnings. It is the midpoint between the nearest benign score (70.1%) and scam score (72.3%). Those calibration inputs are not independent validation, and this is not a production safety threshold. Reproduce with `python scripts/calibrate_demo_threshold.py`.

Every eligible pattern is ranked under Exact (100%), Very strong (90–under 100%), Strong (80–under 90%), Partial (71.2–under 80%), or Below threshold. The tier boundaries are descriptive display bands, not separately validated fraud decisions. Below-threshold comparisons are not detected matches. No known match does not prove safety. Read `docs/DEMO_SCAM_PATTERNS.md` for all full texts and demonstration queries.

```text
.venv\Scripts\python scripts/seed_demo_patterns.py
.venv\Scripts\python scripts/verify_demo_patterns.py http://127.0.0.1:8000
```

The current API is unauthenticated and must stay private/local. No new trained AI weights are included; existing legacy assets are retained but not misrepresented as an active detector.
