"""Vercel entry point: the FastAPI app in backend/app/main.py as one Python
function. vercel.json rewrites /api/*, /health*, /docs, /redoc and
/openapi.json here (FastAPI sees the original path); every other route is the
React site built from "front end/". No backend code lives here.
Locally run `python backend/run_server.py` from the repository root.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import create_tables  # noqa: E402
from app.main import app  # noqa: E402,F401  (Vercel serves this ASGI app)

# Serverless platforms may not run FastAPI's startup event, so make sure the
# tables exist on each cold start. If the database is briefly unreachable,
# the API still starts and /health still answers.
try:
    create_tables()
except Exception as exc:  # pragma: no cover - depends on the database
    # Driver error strings may contain connection details; log only the type.
    print(f"[trustgraph] create_tables failed at cold start: {type(exc).__name__}", file=sys.stderr)
