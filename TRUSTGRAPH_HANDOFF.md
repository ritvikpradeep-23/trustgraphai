# TrustGraph continuation guide

## Current canonical layout

- `front end/`: React + Vite application; built assets go to `front end/dist/`.
- `backend/app/`: complete FastAPI application, schemas, SQLAlchemy models, services, API routes and fingerprint package.
- `backend/run_server.py`: local launcher. Root `run_server.py` and `requirements.txt` are compatibility forwarders.
- `trustgraph_extension/`: complete Manifest V3 extension, settings, content scripts and tests.
- `data/`, `scripts/`, `docs/`, `tests/`: public synthetic catalog, seed/import/calibration tools, documentation and verification.
- `api/index.py`: tiny upstream compatibility deployment shim, updated to import from `backend/`. Root Vercel Services config does not use it.
- `web-app/` and `browser-extension/`, if present, are older prototypes, not the canonical frontend/extension.

The old root `app/` is gone, not the backend: 30 of 31 original source files were moved to `backend/app/`. The obsolete SQLite fingerprint health route was replaced by PostgreSQL `/health/database` upstream. Do not recreate a competing root backend.

## Detection and dataset

Scam messages use deterministic normalized token-Jaccard and sequence similarity against PostgreSQL report texts. No AI service, AI URL, model download or external text analysis is required. Every eligible report is ranked; qualified matches are distinct from the full comparison list.

The catalog contains 300 distinct synthetic example messages: 36 authored demos plus 264 redacted Hindi/Hinglish synthetic fraud messages from the MIT-listed Hugging Face dataset `sidzzz07/scamshield-dataset`. This is not the official Singapore ScamShield service, not 300 different scam mechanisms and not a verified real-incident collection. Source revision, file checksum, selection rules and licensing are in `data/SCAMSHIELD_NOTICE.md` and `data/scamshield_provenance.json`. The complete judge list is in `docs/DEMO_SCAM_PATTERNS.md` and `docs/SCAMSHIELD_SAMPLE.md`.

The calibrated threshold is 0.712 (71.2% text similarity). Tiers are exact (100%), very strong (90–<100%), strong (80–<90%), partial (71.2–<80%) and below threshold. Exact copies legitimately score 100%; paraphrase results vary naturally. Similarity is not a fraud probability. No match means UNKNOWN, not safe. Calibration uses 13 unseeded English paraphrases and 16 benign controls; this is not an independent accuracy evaluation and does not establish multilingual accuracy. See `docs/DEMO_SCAM_PATTERNS.md`.

AI-written text and video/deepfake checks come from the trained engines in `backend/app/ai/`, behind the single `TrustGraphAI.analyze` boundary in `backend/app/services/ai_model.py`. An engine answers only when its packages are installed (`pip install -r requirements-ai.txt`, kept out of the Vercel requirements) AND its trained model exists on that computer: `models/text_detector/` (fine-tuned distilroberta-base, `train_text.py`) and `models/efficientnet_head.pt` (EfficientNet-B0 + trained real/fake layer, `train_video.py`). Otherwise the exact "pending" answers are returned. No weights are committed, so the hosted deployment stays "pending". Cryptographic C2PA verification remains unavailable. Do not turn unavailable responses into invented scores. Engine and routine tests are in `tests/engine/` and are skipped when the AI packages are missing; `tests/conftest.py` hides any locally trained model from the website tests.

## Backend routes and persistence

`backend/app/main.py` registers all routers. Routes include:

- Health: `GET /health`, `GET /health/database`.
- Core: `POST /api/submit`, `POST /api/detect`, `GET /api/detections`, `GET /api/detections/{id}`, `POST /api/reports`, `GET /api/reports`, `GET /api/reports/{id}`.
- Workspace: `/api/workspace/*`; legacy extension scoring: `POST /api/score`.
- Optional boundaries: `POST /api/text/ai-check`, `POST /api/video/analyze`, `POST /api/provenance/analyze`.
- Deterministic features: `POST /api/url/analyze`, `POST /api/relationships`, `GET /api/relationships`, `POST /api/media/check`.

PostgreSQL only: set private `DATABASE_URL`, or `POSTGRES_URL` as fallback. Plain postgres/postgresql URLs select installed psycopg automatically. SQLAlchemy uses pooled-connection pre-ping. Never commit credentials or use a frontend VITE-prefixed database variable.

Tables: submissions, detections, reports, report_matches, relationships and fingerprints. Existing rows are preserved; catalog seeding is idempotent and validates collisions before writing. `Base.metadata.create_all` creates missing tables, not schema migrations. No migration framework exists.

URL analysis parses locally without fetching the site. Registrable domains use a limited suffix heuristic, not a full public-suffix database. Provenance inspection finds metadata/manifest presence but does not verify signatures. Explicit correlation validates relationships between existing entities; automatic graph discovery is not implemented.

Image fingerprints use perceptual hashes, four indexed 16-bit bands and PostgreSQL storage; images/frames are decoded in memory, not retained. Optional limits are defined in `backend/app/fingerprint/config.py`. Fingerprint demo seeding is separate from the scam catalog and is not necessary for message matching.

## One Vercel project

The canonical root `vercel.json` uses Vercel Services: Vite frontend rooted at `front end/`, FastAPI backend rooted at `backend/` with `app.main:app` entrypoint. Ordered rewrites route API, health and docs to the backend while preserving paths; extensionless frontend navigation receives the SPA fallback. Missing API/asset paths must not become HTML.

Import the whole repository as one project with Root Directory `.`, not either subfolder. Use Services support and remove conflicting old dashboard build overrides. Set private database configuration, `VITE_USE_MOCK=false` and `VITE_API_BASE_URL=/api`. See `docs/VERCEL_DEPLOYMENT.md` for settings and post-deployment checks. No Vercel account settings, secrets or cloud deployment were changed here.

Keep Deployment Protection enabled until authentication/authorization is implemented. Do not expose raw submissions/history publicly. Extension access to a protected deployment requires an authorized plan; no bypass is supplied. The unpacked extension defaults to a local backend URL and must be configured separately for an authorized hosted URL.

## Local setup and checks

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
# Create private .env from .env.example and configure PostgreSQL locally.
python scripts/seed_demo_patterns.py
npm ci --prefix "front end"
npm run build --prefix "front end"
python backend/run_server.py
```

The default local API/site port is 8000; set PORT for a different port. For hot-reload frontend development use `npm run dev` in `front end/`; its development proxy is not a production deployment solution.

Checks:

```powershell
python -m pytest tests -q
npm test --prefix "front end" -- --run
python scripts/check_vercel_config.py
```

Fingerprint DB integration fixtures require a separate throwaway `TEST_DATABASE_URL`; never point them at the existing demonstration database. Schema validation/local builds do not prove a cloud deployment. Inspect the extension test scripts under `trustgraph_extension/test/` before running live-browser or DB-dependent tests.

## Continuation rules

Read this guide and inspect current git status before editing. Preserve existing user changes and remote commits. Keep backend implementation in `backend/`, PostgreSQL only, secrets private, matching explanations honest, no invented AI scores and no automatic dataset overwrite. Maintain tests for API JSON paths, SPA deep links, varied similarity, catalog uniqueness and deployment layout.
