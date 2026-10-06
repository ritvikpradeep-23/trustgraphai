# Backend

Canonical FastAPI source is in `backend/app/`. The root `app/` contains only a compatibility import shim so old commands and tests keep working.

This backend belongs to one combined repository with `front end/`, `trustgraph_extension/`, and shared root `data/`, `scripts/`, `tests/`, `models/`. Do not upload only this subfolder: the runnable project is the whole repository / combined ZIP.

From the root, install `backend/requirements.txt`, configure the ignored root `.env`, build `front end/`, and run `python backend/run_server.py` or `python run_server.py`.

Message checks use PostgreSQL pattern matching, not AI. `POST /api/detect` is the website contract; `POST /api/score` adapts the complete browser extension's existing scorer. No known match returns 503 for the extension, activating its existing local-rule fallback rather than declaring safety. Account pairing/sync is not implemented.

Existing model assets and training source remain in the repo as legacy/optional components. They are not automatically connected to this API. AI-written/media endpoints honestly remain unavailable without an implemented engine.
