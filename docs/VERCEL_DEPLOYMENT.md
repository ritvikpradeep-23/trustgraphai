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
4. Deployment Protection: while it is on, only signed-in Vercel users can open the site, and the browser extension's requests are rejected (it falls back to its on-device rules and can't pair). For a demo, turn it off or demo locally; this API has no user accounts, so anyone with the link can use it while it's off.

## Checks after deploying

- `/health` → `{"status": "ok"}`; `/health/database` → `{"ok": true, ...}`.
- `/app/analyze` and `/app/analytics` load directly (deep links).
- `/api/unknown` → a JSON 404 from FastAPI, not the site.
- Analyze a non-sensitive test message.

## Verified here (not on Vercel)

The uploaded file set (repository minus `.vercelignore`) was copied, built with the exact install/build commands, the function's `api/requirements.txt` installed into a fresh environment, and served with `vercel.json`'s rewrites against PostgreSQL 16: health, database round trip, workspace status, docs, pairing codes, deep links and asset 404s all behaved as above. A real Vercel build log is still the final check.
