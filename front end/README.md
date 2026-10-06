# TrustGraph frontend

React/TypeScript dashboard in the requested `front end/` folder. Live mode is the default and connects to the repository's FastAPI backend, not the Emergent preview.

## Run the combined application

From the repository root (Python 3.11+, Node.js 22.18+):

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
cd "front end"
npm ci
npm run build
cd ..
.venv\Scripts\python run_server.py
```

Before starting, create a local root `.env` using `.env.example` and configure `DATABASE_URL`. Use the SQLAlchemy `postgresql+psycopg://` scheme and your provider's SSL settings. Never put database credentials in a frontend environment variable or commit them.

Open http://127.0.0.1:8000/app/dashboard. FastAPI serves the built frontend and API from one origin, including refreshes on nested routes.

For development, leave the backend running and run `npm run dev` from this folder. Vite proxies `/api` to port 8000; set the shell variable `TRUSTGRAPH_API_URL` for another local backend address. The client API prefix is controlled by `VITE_API_BASE_URL` (default `/api`). Restart/rebuild after environment changes.

## Connected features and limits

- Dashboard, search, risk/date filters, detail views, and analytics read sanitized PostgreSQL detection history through `/api/workspace/detections`.
- The projection omits stored submission text, captions, sender identities, media references, and full URL paths/query strings. Backend explanation text is still displayed.
- Run `python scripts/seed_demo_patterns.py` from the repository root to add 300 explicitly synthetic examples (36 original + 264 redacted ScamShield messages), idempotently. Full texts: `docs/DEMO_SCAM_PATTERNS.md` and `docs/SCAMSHIELD_SAMPLE.md`. Provenance/license: `data/SCAMSHIELD_NOTICE.md`.
- Analyze calls existing `POST /api/detect` and `POST /api/url/analyze`. It does not submit or persist messages. The existing detect API does not save results; an analysis response will not appear in history.
- Message checking needs no AI: it compares text with PostgreSQL scam reports using normalized token overlap and sequence similarity (demo-calibrated threshold 71.2%). Every eligible pattern is ranked in resemblance tiers. A match is HIGH with a text-similarity score, not a calibrated fraud probability. No match is UNKNOWN, never a safety verdict. URL structure checks do not establish website safety.
- This is an **unauthenticated, private/local prototype**, not a production account system. There is no per-user history isolation. Do not publish the backend without real authorization and a security review. CORS is not authentication.
- Workspace name and time-estimate preferences are browser-local. Notifications, password changes, pairing keys, feedback/review, history deletion, and account deletion are disabled because the backend does not implement them.
- JSON export contains projected history and local preferences. The contact form remains a labelled local demo and does not send messages.
- Optional offline demo: set `VITE_USE_MOCK=true` and rebuild/restart. Demo sign-in is simulated; never enter real passwords. Analyze requires live mode.

## Verify

```text
npm test
npm run build
```

Fourteen Node regression tests cover filtering, pagination, analytics, pending scores, demo storage, and local preferences. See `docs/WORKSPACE_INTEGRATION.md` in the repository root for backend verification and integration details.
