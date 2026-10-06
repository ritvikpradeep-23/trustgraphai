# TrustGraph Continuation Guide

## Purpose and architecture

TrustGraph is a scam-content analysis API with a small Next.js web app and a Manifest V3 browser extension. The backend is FastAPI, with Pydantic request/response schemas and SQLAlchemy persistence on PostgreSQL. `app/main.py` registers API routers and creates declared tables at startup. No migration framework is present.

## Phase status in the current implementation

There is no phase roadmap/status file in the repository, so status below describes code present, not project-wide completion claims.

- **Core submissions, detection history, reports and previous-report matching:** implemented.
- **Phase 13 URL/domain analysis:** implemented as a deterministic parser and endpoint; see limitations below.
- **Provenance/C2PA inspection:** implemented as bounded metadata/container inspection; cryptographic verification is unavailable.
- **Phase 15 scam graph/correlation:** partial relational foundation. Typed relationship records can be created and listed, with deterministic checks. Relationships are not automatically discovered/populated and the model is not a graph database.
- **AI/model integration:** adapter boundaries and explicit unavailable responses exist; no detector is connected.
- **Web app and browser extension:** basic analyze/history experience exists; neither exposes Phase 13/15 features.

## Repository map

- `app/main.py` — FastAPI app, router registration, startup table creation, `/health`.
- `app/api/` — route modules: `detect.py`, `submission.py`, `report.py`, `detection_history.py`, `ai_detectors.py`, `provenance.py`, `url_analysis.py`, `relationships.py`.
- `app/core/database.py` — PostgreSQL engine/session, SQLAlchemy models, `Base.metadata.create_all`.
- `app/schemas/` — Pydantic schemas for submissions, detections, reports and provenance.
- `app/services/` — detection adapters/model boundary, submission processing, previous-report matching, URL analysis, provenance parsing, correlation validation.
- `tests/` — unittest endpoint and service tests: AI boundaries, provenance, relationships, URL analysis.
- `web-app/` — Next.js app (`app/page.tsx`, `app/dashboard/page.tsx`), backend proxy routes under `app/api/`, backend URL helper in `lib/backend.ts`.
- `browser-extension/` — popup UI, config, manifest and client-side `/api/detect` request.
- Root `requirements.txt`, `.env.example`; `web-app/package.json`, `web-app/.env.local.example`.

## Backend API

- `GET /health`
- `POST /api/submit`
- `POST /api/detect`
- `GET /api/detections`
- `GET /api/detections/{detection_id}`
- `POST /api/reports`
- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `POST /api/text/ai-check`
- `POST /api/video/analyze` (multipart file)
- `POST /api/provenance/analyze` (multipart file)
- `POST /api/url/analyze`
- `POST /api/relationships`
- `GET /api/relationships` (optional `entity_type`, `entity_id`, `relationship_type` query filters)

## PostgreSQL schema

`DATABASE_URL` is mandatory; `app/core/database.py` passes it to SQLAlchemy `create_engine`. Requirements include `psycopg[binary]`. No SQLite fallback/configuration is present.

- `submissions` (`submission_id` PK): source/content type, text/caption, URL, media reference, sender, source timestamp, consent and creation time.
- `detections` (`detection_id` PK): FK to submission, score/level, JSON signals/reasons and timestamp.
- `reports` (`report_id` PK): FK to submission, report type/status and timestamp.
- `report_matches` (`match_id` PK): FKs to candidate submission, report and matched submission; similarity score and timestamp. Unique `(submission_id, report_id)` prevents repeat matches.
- `relationships` (`relationship_id` PK): relationship type, typed source/target IDs, JSON evidence and timestamp. Check constraints restrict relationship types to `similar_content`, `same_reported_content`, `same_sender`, `same_url_domain`, `related_report`; entity types to submission/report/detection. Unique canonicalized edge constraint prevents duplicate unordered edges. Entity IDs are polymorphic strings, not foreign keys.

There are no separate sender, URL/domain, or content tables. Relationships are recorded between existing submission/report/detection entities, with matching evidence stored on the edge. The correlation endpoint validates stored values before insertion.

## URL/domain analysis

`app/services/url_analysis.py` uses Python URL parsing, IDNA and IP parsing only; there are no outbound requests. It accepts a bare domain by prepending HTTPS, permits HTTP(S), normalizes host/scheme, removes userinfo and fragments from returned normalized URL, and extracts hostname, estimated registrable domain, port, path and query. Deterministic signals: HTTP, IP hostname, unusual port, more than three subdomains, suspicious encoding/pattern, URL length over 2048, embedded userinfo. Inputs over 4096 characters and malformed/unsupported URLs are rejected. Registrable-domain extraction uses a small hard-coded multi-label suffix list, not a complete public suffix database; treat it as heuristic.

## Provenance and C2PA

`app/services/provenance.py` inspects uploaded files locally with a 50 MiB analysis limit, safe basename handling, content-signature detection, and supported metadata/container readers (including PNG, JPEG, PDF, DOCX and common media signatures). It extracts selected metadata and detects a C2PA manifest-store identifier in a JUMBF description. This is presence/metadata inspection only: `c2pa_verified` remains unavailable (`null`); no claim signature validation is implemented. Unsupported or malformed files return unavailable results/warnings. No external calls are made.

## Correlation

`app/services/correlation.py` validates shared sender, registrable URL domain, exact normalized content, thresholded similar content using `previous_report_matcher` (`MATCH_THRESHOLD = 0.72`), and reports attached to the same submission. `POST /api/relationships` accepts typed source/target entities and a relationship type, rejects unsupported/unsubstantiated edges and canonicalizes endpoint order. `GET` lists edges with filters. Relationship writes are explicit API calls, not automatic graph discovery. `related_report` currently means two reports share the same submission.

## AI architecture and connection status

- `TrustGraphAI` in `app/services/ai_model.py` is the existing scam detector boundary. It always returns the pending fallback: zero-valued signals/score, `LOW`, and `AI model integration pending`.
- `ScamDetectorAdapter` preserves that interface for `/api/detect`. Detection also checks previous report matches; no trained scam model is bundled.
- `AIWrittenTextAdapter` and `VideoDeepfakeAdapter` define injectable protocols. With no engine connected, their endpoints return `available: false`, `score: null`, and explicitly say no score was produced.
- Future integrations can be supplied as adapter engines (`AIWrittenTextEngine.analyze(text)` and `VideoEngine.analyze(video)`), or implement the existing `TrustGraphAI.predict(channel, sender, text, url)` boundary. Do not report a score as available unless a real engine returns it.

## Web app and extension

The Next.js app provides a text analyze form and a dashboard for detections/reports/details. Its server routes proxy detection POST and detection/report GET calls to the backend. It does not currently expose URL analysis, provenance or relationship APIs. Run scripts are `dev`, `build`, `start` in `web-app/package.json`.

The browser extension is a user-triggered popup: paste text, call backend `/api/detect`, display risk/reasons/previous matches. Its `config.js` points to `http://127.0.0.1:8000`; manifest host permissions include localhost and loopback only. No URL scanning of visited pages is implemented.

## Setup and verification

PowerShell example from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL in .env to a PostgreSQL DSN; do not commit credentials.
uvicorn app.main:app --reload
python -m unittest discover -s tests -v
python -m compileall -q app tests
```

Web app: `cd web-app; npm install; Copy-Item .env.local.example .env.local; npm run dev`. The optional `TRUSTGRAPH_API_URL` defaults to `http://127.0.0.1:8000`.

Extension: load `browser-extension/` as an unpacked extension in a Chromium-based browser while the backend is running at its configured local URL.

Environment variables evidenced by templates/code:

- `DATABASE_URL` — required PostgreSQL SQLAlchemy DSN; value must be supplied locally.
- `TRUSTGRAPH_API_URL` — optional web-app backend URL; defaults to `http://127.0.0.1:8000`.

## Known limitations and next steps

- No schema migration tool; `create_all` creates missing tables but does not migrate existing table definitions. Add a migration strategy before future incompatible schema changes.
- Relationship records have no polymorphic foreign keys and are created only when clients request them. Consider a safe automatic correlation workflow and stronger referential integrity before treating this as a complete graph.
- Domain extraction is heuristic (small suffix list); improve with a maintained public suffix source only if adding that dependency/data is explicitly approved for the project.
- No detector is connected and current scam risk output is a placeholder. Keep unavailable/fallback status truthful until real detector implementations and evaluation are supplied.
- C2PA detection does not validate signatures/manifests; do not label media authentic based on current output.
- Add integration tests against PostgreSQL for schema creation, relationship uniqueness under concurrent requests, and endpoint persistence; current tests use mocked sessions for DB-backed route behavior.
- Phase/roadmap history is absent from the repo. Confirm the intended next phase from project owners before starting phase-specific work.

## START HERE — Codex on another PC

```text
Read TRUSTGRAPH_HANDOFF.md and inspect the current repository before editing.
Use PostgreSQL only; never add SQLite fallback. Preserve existing routes and contracts.
Treat TrustGraphAI, AI-written detection, video/deepfake detection, and C2PA verification as unavailable unless a real implementation is present.
Do not infer phase status beyond files/tests in the checkout. Ask for or locate the project roadmap before choosing the next phase.
For an approved change, add focused unittest coverage and run:
  python -m unittest discover -s tests -v
  python -m compileall -q app tests
```
