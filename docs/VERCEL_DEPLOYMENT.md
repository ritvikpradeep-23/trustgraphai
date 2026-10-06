# One Vercel project, two services, one domain

The backend was moved, not discarded: source is in `backend/app/`. Comparing the old tree shows 30 of 31 original files remain there. The one removed file, `api/fingerprint_health.py`, was an obsolete SQLite health endpoint replaced by the upstream PostgreSQL `/health/database` implementation. Other database/schema/routes remain present.

The original deployment issue could still occur before this change: there was no Vercel config, and selecting only `front end/` omits the Python backend. The Vite development proxy also does not run in production.

The root `vercel.json` now uses Vercel Services: frontend is built from `front end/`, backend from `backend/` with ASGI entrypoint `app.main:app`. Top-level rewrites send `/api`, health and API docs to the backend before the frontend catch-all. The original `/api` path is preserved. The frontend has a navigation fallback for extensionless SPA routes, while asset requests are not rewritten to HTML.

## Settings you must choose in Vercel

1. Import the whole `trustgraphai` repository as ONE project. Root Directory must be the repository root (`.`), NOT `front end/` or `backend/`. Do not create a separate project for each folder.
2. Use Services support (currently beta). Let the root config control service-specific framework, install, build, and output settings. Remove conflicting old dashboard overrides.
3. Set `DATABASE_URL` privately in Vercel's backend environment (`POSTGRES_URL` is also supported as a fallback). Plain `postgres://` and `postgresql://` URLs select the installed psycopg driver automatically. Never use `VITE_DATABASE_URL` or commit a connection string. Use the appropriate hosted PostgreSQL connection/pool configuration and TLS; do not disable certificate verification.
4. Keep `VITE_USE_MOCK=false` and `VITE_API_BASE_URL=/api`. There is no localhost API URL on a deployed frontend. Same-origin API calls need no broad CORS setting.
5. Preserve database tables; run the catalog seed locally against the configured database before the demo. Do not seed or train during a Vercel build. Local files are not persistent serverless storage.
6. Keep Deployment Protection enabled while this API lacks authentication. Do not publish a public production service with raw submissions/history endpoints. Browser extension calls to protected deployments may need a separate authorized access plan; no protection bypass is built in.

`.vercelignore` excludes local credentials, private datasets/backups, caches, dependencies, optional legacy model/training collections, and the browser extension from the serverless deployment. The complete source ZIP still includes the extension and public catalog. Messages use the PostgreSQL catalog, not a runtime JSON file.

## Verification boundaries

The upstream `api/index.py` compatibility shim is retained and now imports from `backend/`, but it is not the configured Services entrypoint. All actual backend implementation remains in `backend/app/`; the old root `app/` folder must not be restored. The upstream PostgreSQL URL normalization and stale-connection pre-ping fix are preserved.

Local checks validate entrypoint import from the backend root, configured services/routes, `/api` JSON behavior, SPA deep links, database matching, and frontend production build. They cannot prove a cloud deployment without Vercel project access/build logs. No deployment, project setting, or secret was changed on Vercel by this task.

After you deploy the updated commit, verify `/app/analyze` and `/app/analytics` directly, `/health`, `/api/workspace/status`, and a non-sensitive test message in Analyze. `/api/unknown` must return a backend JSON 404, not the SPA. If Services is unavailable on your project, stop and resolve that configuration; simply selecting the frontend subfolder repeats the original problem.

Sources checked October 6, 2026: [Vercel Services](https://vercel.com/docs/services), [service configuration](https://vercel.com/docs/services/config-reference), [service routing](https://vercel.com/docs/services/routing), [FastAPI entrypoint](https://vercel.com/docs/frameworks/backend/fastapi).
