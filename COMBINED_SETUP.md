# One repository, one upload

Layout:

```text
backend/                 FastAPI source, requirements, launcher
front end/               Complete React/Vite frontend
trustgraph_extension/    Complete browser extension (96 tracked files)
models/                  Existing legacy model assets (not a new AI engine)
src/, training/, routine/ Existing optional legacy engine/training sources
data/                    Synthetic scam catalog and separate judge paraphrases
scripts/, tests/         Database seeding and verification
app/, run_server.py      Compatibility shims for old commands
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

Its remote score endpoint is now implemented. When no database match is available, existing on-device rules are used. Account pairing/history sync remains unavailable; extension-local history works separately. No extension install or browser permission was performed automatically.

## Dataset and honest score variation

36 authored synthetic scam examples are seeded additively in PostgreSQL (up from 12); repeated seeding makes no duplicates. Twelve separate unseeded judge queries paraphrase stored examples. Their measured similarities vary naturally. Exact normalized copies still correctly score 100% similarity: scores are never randomized or capped for appearance.

The score is word/sequence similarity, not fraud probability or a claim of AI accuracy. A 72% threshold triggers a known-pattern match. No known match does not prove safety. Read `docs/DEMO_SCAM_PATTERNS.md` for all full texts and demonstration queries.

```text
.venv\Scripts\python scripts/seed_demo_patterns.py
.venv\Scripts\python scripts/verify_demo_patterns.py http://127.0.0.1:8000
```

The current API is unauthenticated and must stay private/local. No new trained AI weights are included; existing legacy assets are retained but not misrepresented as an active detector.
