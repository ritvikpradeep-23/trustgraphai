"""Vercel entry point: the whole FastAPI app (app/main.py) as one Python
function. vercel.json sends /api/*, /health* and the API docs here; FastAPI
sees the original path, so every route works unchanged. Everything else is
the React site in "front end/" (built to static files).

Locally nothing changes: run `uvicorn app.main:app` as before.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import create_tables  # noqa: E402
from app.main import app  # noqa: E402,F401  (Vercel serves this ASGI app)

# Serverless platforms may not run FastAPI's startup event, so make sure the
# tables exist on each cold start. If the database is briefly unreachable,
# the API still starts and /health still answers.
try:
    create_tables()
except Exception as exc:  # pragma: no cover - depends on the database
    print(f"[trustgraph] create_tables failed at cold start: {exc}", file=sys.stderr)
