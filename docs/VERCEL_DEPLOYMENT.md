# One Vercel project, one domain

The root `vercel.json` makes the repository ONE ordinary Vercel project (no beta "Services" needed):

- **Website:** `npm ci` / `npm run build` in `front end/`, served as static files from `front end/dist`.
- **API:** `api/index.py` is one Python function that serves the FastAPI app from `backend/app/main.py` (no backend code lives in `api/`). Its dependencies are `api/requirements.txt`, kept identical to `backend/requirements.txt` by `tests/test_vercel_layout.py`.
- **Routing:** `/api/*`, `/health`, `/health/*`, `/docs`, `/docs/*`, `/redoc` and `/openapi.json` are rewritten to the function, which sees the original path. Every other extensionless path (`/`, `/app/analyze`, `/app/detections/<id>`, ...) serves `index.html`. Built files are served first; a missing asset (`/assets/x.js`, `/favicon.ico`) is a 404, never HTML.

An earlier version used Vercel Services (beta). On projects without Services it deploys nothing, and every URL shows Vercel's own "404: NOT_FOUND" page. That's why this layout is used.

## Settings in Vercel

1. Import the whole `trustgraphai` repository as ONE project: Root Directory `./` (not `front end/` or `backend/`). Framework Preset: **Other**. Leave Build/Output/Install command overrides **off** (vercel.json sets them). If the project was created with Services, open Settings → Build and Deployment and set the preset to Other.
2. Add a hosted PostgreSQL database (Storage → Neon) or set `DATABASE_URL` (or `POSTGRES_URL`) privately in Environment Variables. Plain `postgres://` / `postgresql://` URLs are converted to the psycopg driver. Never use a `VITE_*` variable or commit a connection string. `127.0.0.1` addresses won't work on Vercel.
3. Redeploy. Seed the catalog once from your PC against the same database: `python scripts/seed_demo_patterns.py`. Do not seed during a Vercel build.
4. Real workspace accounts are now required for history and pairing. Session cookies are Secure automatically on Vercel; keep the frontend and API on the same HTTPS origin. Legacy unowned submission/report/history/relationship endpoints are blocked in hosted mode. Configure authentication, rate limiting, trusted proxy handling and security review before any public launch.
5. Deployment Protection can reject extension requests even after account pairing. Demo locally if it is enabled. Changing protection is a user/administrator decision; no protection setting has been changed here.

## Model availability

The function now installs the CPU scam runtime by default: pinned numpy, scipy, joblib, pandas and scikit-learn, with Python 3.12 in `.python-version`. It uploads `src/trustgraph/`, `models/anomaly_isolation_forest.joblib` (~1.4 MB), `models/risk_bands.json` and `data/precedent/reports.json` (public synthetic identifiers). `.vercelignore` keeps all other data and model directories out, including private reports, training inputs, rejected candidates and media weights. `excludeFiles` no longer discards the required precedent file.

Records-first order is unchanged: a qualifying PostgreSQL match skips the model; otherwise the original engine produces the final review score. No Torch, Hugging Face download, external provider or new training is required for scam messages. The model still has false negatives/positives; inference availability is not proof of accuracy.

`tests/test_scam_model_bundle.py` stages the actual tracked/new file set using ignore rules and function exclusions, then runs eight genuine inference API cases in an isolated subprocess, with no access to the original source tree or real database. Missing model, bands or precedent files produce unavailable/503, not fabricated scores. This verifies local packaging, **not** Linux dependency installation, Vercel bundle size, cold-start latency or a cloud deployment. The final build log and `/health/scam-model` on the deployed domain are still required. Do not install optional heavyweight media requirements into this function.

## Checks after deploying

- `/health` → `{"status": "ok"}`; `/health/database` → `{"ok": true, ...}`; `/health/scam-model` → HTTP 200 with `inference: "verified"`. A 503 means model inference is unavailable even if the website loads.
- `/login` and `/signup` load directly; protected `/app/analyze` and `/app/analytics` require an account.
- `/api/unknown` → a JSON 404 from FastAPI, not the site.
- Analyze a non-sensitive test message.

## Verified here (not on Vercel)

Local API entrypoint, deep-link/asset routing and isolated scam-model upload-file inference checks pass. Real PostgreSQL account-scoped persistence and records-first/model-second checks use a temporary schema and roll everything back. No cloud build/deployment was performed; a real Vercel build log remains the final check.
