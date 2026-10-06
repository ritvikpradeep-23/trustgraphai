# React workspace + PostgreSQL backend

The React application lives in `front end/`. FastAPI serves its generated `dist/` output and its existing API on the same origin. Existing submission, detection, report, provenance, URL, and relationship routes are preserved. No database models or stored records were changed by this integration.

## Start

Follow `front end/README.md`. Configure root `.env` locally, then build the frontend and run `python run_server.py`. The launcher binds only to 127.0.0.1. API documentation is at `/docs`.

Only `.env.example` is committed; `.env`, frontend `.env.local`, dependencies, virtual environments, and build artifacts remain ignored. Never put `DATABASE_URL` in a `VITE_*` variable. Rotate any credential shared in chat.

## Adapter contract

- `GET /api/workspace/detections`: read-only frontend DTOs. Existing `/api/detections` contracts remain unchanged.
- `GET /api/workspace/detections/{id}`: projected detail or JSON 404.
- `GET /api/workspace/status`: API reachability, explicitly no authentication or pairing. Message checks use deterministic database matching; AI modalities remain unavailable.

The projection maps MEDIUM to CAUTION and unsupported/invalid scores to PENDING. It excludes raw submission fields and returns only a URL hostname. Historical backend explanation strings are retained. Current history is unpaginated at the API; the frontend filters/paginates it in memory. Add server-side pagination before large deployments.

Message analysis calls `/api/detect` without a submission ID: previous-report matching reads the database, but no message/result is persisted. URL analysis is deterministic and does not make outbound requests. Text checks now use the existing report matcher directly, without AI. Scores are text similarity, not fraud probability. UNKNOWN means no known match, not safe. Seed 12 synthetic examples using `python scripts/seed_demo_patterns.py`; verify via `python scripts/verify_demo_patterns.py` against the running API. No account tokens or pairing status are produced.

## Verification

`python scripts/check_workspace_database.py` runs a read-only SELECT 1 and checks expected tables without printing credentials. It does not seed or delete data.

Install `requirements-dev.txt`, then run current backend tests with a dummy PostgreSQL DSN (database dependencies are mocked):

```powershell
$env:DATABASE_URL='postgresql+psycopg://test:test@127.0.0.1:5432/test'
.\.venv\Scripts\python -m pytest -q --ignore=tests/test_fingerprint.py
Remove-Item Env:DATABASE_URL
```

`tests/test_fingerprint.py` belongs to an older removed backend and imports nonexistent `app.config` / `create_app`; it must be migrated separately. The targeted suite does not verify that legacy subsystem.

Workspace tests use fake sessions, never the configured database. They verify omitted private fields, pending/null semantics, existing routes, CORS, static SPA handling, and missing-asset/API 404s. Frontend tests cover live data calculations and local preferences as well as optional demo behavior.

## Deployment limits

No authentication or per-user authorization is implemented by the backend. Do not expose it to the internet as-is. Existing raw API endpoints can return submission data; the sanitized view is not an access-control boundary. Disabled frontend buttons also are not authorization.

AI-written/media detection, extension pairing, review/feedback writes, notifications, and account deletion remain unavailable. Analytics reflect stored backend values, not a trained model. Backend startup uses create_all, not migrations. Production needs authorization, migrations, bounded queries, input limits, observability, and trained/validated detectors.
