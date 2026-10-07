# React workspace + PostgreSQL backend

The React application lives in `front end/`; canonical backend source is in `backend/app/`. FastAPI serves its generated `dist/` output and its existing API on the same origin. Existing submission, detection, report, provenance, URL, and relationship routes are preserved. The merged extension backend adds PostgreSQL fingerprint storage; existing stored records are preserved.

## Start

Follow `front end/README.md`. Configure root `.env` locally, then build the frontend and run `python run_server.py`. The launcher binds only to 127.0.0.1. API documentation is at `/docs`.

Only `.env.example` is committed; `.env`, frontend `.env.local`, dependencies, virtual environments, and build artifacts remain ignored. Never put `DATABASE_URL` in a `VITE_*` variable. Rotate any credential shared in chat.

## Adapter contract

- `GET /api/workspace/detections`: signed-in account's metadata DTOs only. Legacy unowned records are preserved but not exposed as account history.
- `GET /api/workspace/detections/{id}`: projected detail or JSON 404.
- `GET /api/workspace/status`: signed-in account's extension state (`CONNECTED` if its authenticated heartbeat is within 2 minutes, otherwise `NOT CONNECTED`), `lastSeen`, pairing and original scam-engine availability.
- `POST /api/workspace/checks`: session/CSRF-protected Analyze request; persists verdict metadata only.

Current account history excludes raw messages, sender identities, model explanation text and URL paths. Legacy projection helpers remain for compatibility but are not used to return unowned records. The API is unpaginated; frontend filtering/pagination does not replace bounded server queries before large deployments.

The web Analyze page now calls `/api/workspace/checks`; the extension uses stateless `/api/detect`. Both combine the original trained anomaly/four-signal engine when installed with catalog matching, otherwise explicitly fall back. Scores are review evidence/text similarity, not calibrated fraud probability. UNKNOWN is not safe. URL structure checks do not make outbound requests or save history. Seed the 300-message synthetic catalog (36 original + 264 ScamShield samples) using `python scripts/seed_demo_patterns.py`. See [current account/model setup](ACCOUNT_EXTENSION_INTEGRATION.md).

## Browser extension ↔ workspace

`backend/app/api/extension_sync.py` implements the contract the extension already spoke (`trustgraph_extension/shared/api-client.js`, `TG.WEBAPP`):

1. Sign in, then workspace **Settings → New code** calls CSRF-protected `POST /api/extension/pairing-code` and shows a one-time code (10 minutes).
2. In the extension popup, the user enters it under "Have a pairing code?". The extension calls `POST /api/extension/pair` and keeps the returned token; the backend stores only its SHA-256.
3. From then on, every verdict the extension saves is synced with `POST /api/results` (Bearer token). It is the extension's Result record only: level, 0-100 score, signal type ids, channel, hostname. The request model forbids extra fields and checks each value's shape, so message text, senders or URL paths are rejected (422). Stored in `extension_results`.
4. Account-owned extension results appear alongside that account's Analyze checks. "Mark as wrong verdict" requires the owning extension's Bearer token and appears as a false alarm. "Open in workspace" opens `/app/detections/<id>`.
5. Authenticated heartbeat (`POST /api/status`, every 15 s on supported sites) drives only the owning account's status. The website refreshes history/analytics/status every 15 seconds.

The extension uses its server URL as the workspace unless Settings → Web app URL says otherwise (on-device-only mode keeps the built-in demo web app). Regression tests: `tests/test_extension_sync.py` (requires a separate disposable `TEST_DATABASE_URL`) and `scripts/verify_account_integration.py` (temporary schema, wholly rolled back). The older browser E2E harness predates account login and was not run as current proof.

Pairing-code issuance now requires a real account session and CSRF token. Pairing tokens are account-owned; old unowned tokens require pairing again. For the precise auth flow and security limits see `ACCOUNT_EXTENSION_INTEGRATION.md`.

## Verification

`python scripts/check_workspace_database.py` runs a read-only SELECT 1 and checks expected tables without printing credentials. It does not seed or delete data.

Install `requirements-dev.txt`, then run current backend tests with a dummy PostgreSQL DSN (database dependencies are mocked):

```powershell
$env:DATABASE_URL='postgresql+psycopg://test:test@127.0.0.1:5432/test'
.\.venv\Scripts\python -m pytest -q -p no:cacheprovider
Remove-Item Env:DATABASE_URL
```

Fingerprint unit tests are included. Seven fingerprint database integration tests require a separate `TEST_DATABASE_URL` and skip when it is absent. Do not point destructive test fixtures at your production database.

Workspace tests use fake sessions, never the configured database. They verify omitted private fields, pending/null semantics, existing routes, CORS, static SPA handling, and missing-asset/API 404s. Frontend tests cover live data calculations and local preferences as well as optional demo behavior.

## Deployment limits

Accounts and per-user history authorization are implemented. Hosted mode blocks legacy unowned submission/report/history/relationship endpoints; local-only administration remains compatible. These changes are not an independent security audit. Keep the prototype restricted until reviewed.

Website checks now support owner-only review/feedback; account-scoped history deletion and password-confirmed account deletion are implemented. Account deletion revokes owned extension tokens. AI-written weights, notifications and email recovery remain unavailable. Synced extension snapshots are read-only in the website. Analytics reflect stored verdict metadata, not recomputed probabilities. Startup uses additive create_all, not versioned migrations. Production still needs migrations, bounded queries, abuse controls, proxy-aware rate limiting, normal extension token expiry/revocation controls, observability and independent detector validation. Vercel packaging now includes baseline CPU scam assets/dependencies, with isolated local bundle inference verified but no cloud build/deployment claim. See `IMPLEMENTATION_AUDIT.md` for current gaps and checks.
