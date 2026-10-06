# TrustGraph frontend

React/TypeScript dashboard in the requested `front end/` folder. Live mode is the default and connects to the repository's FastAPI backend, not the Emergent preview.

## Run the combined application

From the repository root (Python 3.11+, Node.js 22.18+):

```text
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-scam.txt
cd "front end"
npm ci
npm run build
cd ..
.venv\Scripts\python run_server.py
```

Before starting, create a local root `.env` using `.env.example` and configure `DATABASE_URL`. Use the SQLAlchemy `postgresql+psycopg://` scheme and your provider's SSL settings. Never put database credentials in a frontend environment variable or commit them.

Open http://127.0.0.1:8000/signup and create your own account. Login redirects to `/dashboard`, an alias of `/app/dashboard`. FastAPI serves the built frontend and API from one origin, including refreshes on nested routes.

For development, leave the backend running and run `npm run dev` from this folder. Vite proxies `/api` to port 8000; set the shell variable `TRUSTGRAPH_API_URL` for another local backend address. The client API prefix is controlled by `VITE_API_BASE_URL` (default `/api`). Restart/rebuild after environment changes.

## Connected features and limits

- Dashboard, search, risk/date filters, detail views, and analytics read sanitized PostgreSQL detection history through `/api/workspace/detections`.
- History is scoped to the signed-in account, and stores only verdict metadata, not raw messages, senders, media references or URL paths.
- Run `python scripts/seed_demo_patterns.py` from the repository root to add 300 explicitly synthetic examples (36 original + 264 redacted ScamShield messages), idempotently. Full texts: `docs/DEMO_SCAM_PATTERNS.md` and `docs/SCAMSHIELD_SAMPLE.md`. Provenance/license: `data/SCAMSHIELD_NOTICE.md`.
- Analyze calls authenticated `POST /api/workspace/checks` and stateless `POST /api/url/analyze`. Message checks appear in history as verdict metadata; messages and model explanation text are never saved there. URL checks are not saved.
- The original learned anomaly model contributes alongside deterministic continuity, wording similarity, precedent and database matching when installed. The fallback needs no AI and is explicit. Scores are not calibrated fraud probabilities. Exact catalog copies can correctly have 100% text similarity; scores are not randomized. UNKNOWN is not safe. URL structure checks do not establish website safety.
- Accounts use PBKDF2 password hashes and server-side HttpOnly cookie sessions, not browser-storage tokens. See `docs/ACCOUNT_EXTENSION_INTEGRATION.md` for deployment/security limits.
- Time-estimate/display preferences are browser-local. Extension pairing and extension feedback work. Password recovery, notifications, web-side review/delete and account deletion are not configured and are labelled accordingly.
- JSON export contains projected history and local preferences. The contact form remains a labelled local demo and does not send messages.
- Optional `VITE_USE_MOCK=true` switches data views to illustrative mock records, not real history. Login still requires the real backend. Use default live mode for the integration.

## Verify

```text
npm test
npm run build
```

Eighteen Node regression tests cover validation, filtering, pagination, analytics, pending scores, extension channel breakdown, legacy demo storage, and local preferences. The existing theme, BrandMark, NetworkBackdrop, buttons, inputs, icons and React Router were reused; this checkout is Vite/React, not Next.js. See `docs/ACCOUNT_EXTENSION_INTEGRATION.md` for backend verification and setup.
