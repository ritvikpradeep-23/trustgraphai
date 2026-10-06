# React workspace + PostgreSQL backend

The React application lives in `front end/`; canonical backend source is in `backend/app/`. FastAPI serves its generated `dist/` output and its existing API on the same origin. Existing submission, detection, report, provenance, URL, and relationship routes are preserved. The merged extension backend adds PostgreSQL fingerprint storage; existing stored records are preserved.

## Start

Follow `front end/README.md`. Configure root `.env` locally, then build the frontend and run `python run_server.py`. The launcher binds only to 127.0.0.1. API documentation is at `/docs`.

Only `.env.example` is committed; `.env`, frontend `.env.local`, dependencies, virtual environments, and build artifacts remain ignored. Never put `DATABASE_URL` in a `VITE_*` variable. Rotate any credential shared in chat.

## Adapter contract

- `GET /api/workspace/detections`: read-only frontend DTOs. Existing `/api/detections` contracts remain unchanged.
- `GET /api/workspace/detections/{id}`: projected detail or JSON 404.
- `GET /api/workspace/status`: the browser extension's state from its heartbeat (`CONNECTED` if it checked in within 2 minutes, `NOT CONNECTED` after that, `UNKNOWN` before the first one), `lastSeen`, and whether any extension is paired. There is still no user authentication. Message checks use deterministic database matching; AI modalities remain unavailable.

The projection maps MEDIUM to CAUTION and unsupported/invalid scores to PENDING. It excludes raw submission fields and returns only a URL hostname. Historical backend explanation strings are retained. Current history is unpaginated at the API; the frontend filters/paginates it in memory. Add server-side pagination before large deployments.

Message analysis calls `/api/detect` without a submission ID: previous-report matching reads the database, but no message/result is persisted. URL analysis is deterministic and does not make outbound requests. Text checks now use the existing report matcher directly, without AI. Scores are text similarity, not fraud probability. UNKNOWN means no known match, not safe. Seed the 300-message synthetic catalog (36 original + 264 ScamShield samples) using `python scripts/seed_demo_patterns.py`; verify via `python scripts/verify_demo_patterns.py` against the running API. No account tokens or pairing status are produced.

## Browser extension ↔ workspace

`backend/app/api/extension_sync.py` implements the contract the extension already spoke (`trustgraph_extension/shared/api-client.js`, `TG.WEBAPP`):

1. Workspace **Settings → New code** calls `POST /api/extension/pairing-code` and shows a one-time code (10 minutes).
2. In the extension popup, the user enters it under "Have a pairing code?". The extension calls `POST /api/extension/pair` and keeps the returned token; the backend stores only its SHA-256.
3. From then on, every verdict the extension saves is synced with `POST /api/results` (Bearer token). It is the extension's Result record only: level, 0-100 score, signal type ids, channel, hostname. The request model forbids extra fields and checks each value's shape, so message text, senders or URL paths are rejected (422). Stored in `extension_results`.
4. `GET /api/workspace/detections` lists these next to backend detections (`engineVersion: "browser-extension"`), and the detail page shows them. "Mark as wrong verdict" in the extension (`POST /api/feedback`, verdict id only) shows as a false alarm. "Open in workspace" opens `/app/detections/<id>`.
5. The extension's heartbeat (`POST /api/status`, every 15 s on supported sites) drives the dashboard's extension status.

The extension uses its server URL as the workspace unless Settings → Web app URL says otherwise (on-device-only mode keeps the built-in demo web app). Tests: `tests/test_extension_sync.py` (needs `TEST_DATABASE_URL`) and `trustgraph_extension/test/workspace-e2e.js` (real backend + built site + extension in Chromium).

Anyone who can reach this API can create a pairing code: there are no user accounts. Keep it private, as below.

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

No authentication or per-user authorization is implemented by the backend. Do not expose it to the internet as-is. Existing raw API endpoints can return submission data; the sanitized view is not an access-control boundary. Disabled frontend buttons also are not authorization.

AI-written/media detection, workspace-side review/feedback writes, notifications, and account deletion remain unavailable (extension pairing, verdict sync and extension feedback are implemented, see above). Analytics reflect stored backend values, not a trained model. Backend startup uses create_all, not migrations. Production needs authorization, migrations, bounded queries, input limits, observability, and trained/validated detectors.
