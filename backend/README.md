# Backend

All FastAPI source is in `backend/app/`. The old root `app/` is removed; launchers, scripts, and tests resolve the backend package from `backend/`.

This backend belongs to one combined repository with `front end/`, `trustgraph_extension/`, and shared root `data/`, `scripts/`, `tests/`, `models/`. Do not upload only this subfolder: the runnable project is the whole repository / combined ZIP.

From the root, install `backend/requirements.txt`, configure the ignored root `.env`, build `front end/`, and run `python backend/run_server.py` or `python run_server.py`.

Message checks use PostgreSQL pattern matching, not AI. `POST /api/detect` is the website and latest extension contract. It returns every eligible pattern ranked by similarity, with separate tiers and threshold-qualified matches (71.2% demo-calibrated minimum). `POST /api/score` supports older extension clients; no known match returns 503 for that adapter rather than declaring safety. `/api/media/check` performs database fingerprint matching, not AI media analysis. Account pairing/sync is not implemented.

Existing model assets and training source remain in the repo as legacy/optional components. They are not automatically connected to this API. AI-written/media endpoints honestly remain unavailable without an implemented engine.
