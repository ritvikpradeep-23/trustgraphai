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

The default lightweight function intentionally excludes `src/`, `models/` and `data/` and does not install scikit-learn/pandas. Therefore it runs the PostgreSQL catalog fallback, **not** the original trained anomaly model. The full source ZIP retains the model and sources. To run real model inference, use the full combined backend with `requirements-scam.txt` on a suitable Python host; cloud model packaging/limits have not been validated. Do not add heavyweight AI-written/deepfake dependencies and claim a successful Vercel model deployment without checking the actual build and weights.

## Checks after deploying

- `/health` → `{"status": "ok"}`; `/health/database` → `{"ok": true, ...}`.
- `/login` and `/signup` load directly; protected `/app/analyze` and `/app/analytics` require an account.
- `/api/unknown` → a JSON 404 from FastAPI, not the site.
- Analyze a non-sensitive test message.

## Verified here (not on Vercel)

The pre-account static/API layout was previously tested from the upload file set. Current schema validation, API entrypoint, deep-link/asset routing and authentication tests pass locally; real PostgreSQL account/pairing isolation was checked in a rolled-back temporary schema. No cloud deployment or current clean cloud bundle build was performed. A real Vercel build log remains the final check.
