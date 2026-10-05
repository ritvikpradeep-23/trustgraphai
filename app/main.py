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

from app.api import health
from app.config import Settings, get_settings

logger = logging.getLogger("trustgraph")


class ApiError(Exception):
    """Raise anywhere in a request to send {"error": code, "detail": ...}."""

    def __init__(self, status_code: int, error: str, detail: str | None = None):
        self.status_code, self.error, self.detail = status_code, error, detail


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings (e.g. a temp reports file)."""
    settings = settings or get_settings()
    app = FastAPI(title="TrustGraph API", version="0.1.0")
    app.state.settings = settings

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
    return app


app = create_app()
