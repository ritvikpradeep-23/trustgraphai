"""TrustGraph API: one backend for the website, the browser extension and
future messaging bots. Bots and the extension only move content here; all
scam, AI-text and deepfake logic stays in this service.

Run:  python run_server.py            (http://127.0.0.1:8000, what the extension uses)
  or: uvicorn app.main:app --port 8001
"""
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# The project folder (detectors, routine) and src/ (the 4-signal scam engine) must be importable,
# whichever way the server is started.
ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app.ai_text_engine import load_text_detector  # noqa: E402
from app.api import accuracy, ai_text, feedback, health, scam_score, text, video  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.deepfake_engine.face_detector import FaceDetector  # noqa: E402
from app.deepfake_engine.model import load_deepfake_model  # noqa: E402
from app.errors import ApiError  # noqa: E402
from app.scam_engine.embedder import Embedder  # noqa: E402
from app.scam_engine.repository import InMemoryReportRepository  # noqa: E402
from app.scam_engine.service import ScamService  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("trustgraph")


def create_app(settings: Settings | None = None, embedder=None) -> FastAPI:
    """Build the app. Tests pass their own settings (e.g. a temp reports file)
    and a small fake embedder so they don't need the real model."""
    settings = settings or get_settings()
    app = FastAPI(title="TrustGraph API", version="0.1.0")
    app.state.settings = settings
    app.state.scam_service = ScamService(embedder or Embedder(settings.embedding_model_name),
                                         InMemoryReportRepository(settings.reports_path), settings)
    # The deepfake model (if any) and face detector are loaded once at startup.
    app.state.deepfake_model, app.state.deepfake_status = load_deepfake_model(settings)
    app.state.face_detector = FaceDetector(settings.face_margin)
    app.state.ai_text_detector, app.state.ai_text_status = load_text_detector(settings)

    # Browsers block cross-site calls unless the server allows the caller's
    # origin, so the website and the extension must be listed in CORS_ORIGINS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.exception_handler(ApiError)
    def api_error(_: Request, exc: ApiError):
        body = {"error": exc.error}
        if exc.detail:
            body["detail"] = exc.detail
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    def validation_error(_: Request, exc: RequestValidationError):
        # Same {"error": ...} shape as every other error. Only field names and
        # messages are returned, never the submitted text (privacy).
        problems = "; ".join(f"{'.'.join(map(str, e['loc'][1:]))}: {e['msg']}" for e in exc.errors())
        return JSONResponse(status_code=422, content={"error": "invalid_request", "detail": problems})

    app.include_router(health.router)
    app.include_router(scam_score.router)
    app.include_router(text.router)
    app.include_router(ai_text.router)
    app.include_router(video.router)
    app.include_router(accuracy.router)
    app.include_router(feedback.router)
    return app


app = create_app()
