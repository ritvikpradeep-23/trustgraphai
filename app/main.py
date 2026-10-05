"""TrustGraph API: one backend for the website, the browser extension and
future messaging bots. Bots and the extension only move content here; all
scam and deepfake logic stays in this service.

Run:  uvicorn app.main:app --port 8001
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import health, text
from app.config import Settings, get_settings
from app.errors import ApiError
from app.scam_engine.embedder import Embedder
from app.scam_engine.repository import InMemoryReportRepository
from app.scam_engine.service import ScamService

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
    app.include_router(text.router)
    return app


app = create_app()
