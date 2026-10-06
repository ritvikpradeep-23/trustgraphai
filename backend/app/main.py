import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.ai_detectors import router as ai_detectors_router
from app.api.detect import router as detect_router
from app.api.detection_history import router as detection_history_router
from app.api.report import router as report_router
from app.api.relationships import router as relationships_router
from app.api.provenance import router as provenance_router
from app.api.submission import router as submission_router
from app.api.url_analysis import router as url_analysis_router
from app.core.database import create_tables
from app.api.workspace import router as workspace_router
from app.api.extension_score import router as extension_score_router
from app.api.extension_sync import router as extension_sync_router
from app.api.database_health import router as database_health_router
from app.api.media_check import router as media_check_router
from app.api.auth import router as auth_router
from app.api.model_health import router as model_health_router


app = FastAPI(
    title="TrustGraph API",
    description="TrustGraph scam detection backend",
    version="0.1.0",
)

app.include_router(detect_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(detection_history_router, prefix="/api")
app.include_router(report_router, prefix="/api")
app.include_router(submission_router, prefix="/api")
app.include_router(ai_detectors_router, prefix="/api")
app.include_router(provenance_router, prefix="/api")
app.include_router(url_analysis_router, prefix="/api")
app.include_router(relationships_router, prefix="/api")
app.include_router(workspace_router, prefix="/api")
app.include_router(extension_score_router, prefix="/api")
app.include_router(extension_sync_router, prefix="/api")
app.include_router(media_check_router, prefix="/api")
app.include_router(database_health_router)
app.include_router(model_health_router)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exception: RequestValidationError):
    # Pydantic includes invalid input values by default, including passwords.
    # Expose field names/messages only; never echo credentials into API errors.
    return JSONResponse(status_code=422, content={"detail": [
        {key: value for key, value in error.items() if key in {"loc", "msg", "type"}}
        for error in exception.errors()
    ]})


@app.middleware("http")
async def protect_legacy_data(request: Request, call_next):
    # Legacy tables have no owner; do not expose them to new cloud accounts.
    # Local-only administration/seed contracts remain intact.
    hosted = bool(os.getenv("VERCEL")) or request.url.scheme == "https" or os.getenv("AUTH_COOKIE_SECURE") == "true"
    path = request.url.path
    if hosted and any(path == prefix or path.startswith(prefix + "/")
                      for prefix in ("/api/detections", "/api/reports", "/api/submit", "/api/relationships")):
        return JSONResponse(status_code=403, content={"detail": "Legacy unowned records are not exposed by the account workspace."})
    response = await call_next(request)
    if path.startswith(("/api/auth/", "/api/workspace/")):
        response.headers["Cache-Control"] = "no-store"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",") if origin.strip()],
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    allow_credentials=True,
)


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


# Built frontend and API can share one origin. API/docs routes keep their own
# 404 behavior rather than being swallowed by the SPA fallback.
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "front end" / "dist"


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    if any(part.startswith(".") for part in Path(path).parts) or path.split("/", 1)[0] in {"api", "health", "docs", "redoc", "openapi.json"}:
        raise HTTPException(status_code=404, detail="Not found")
    asset = (FRONTEND_DIST / path).resolve()
    if not asset.is_relative_to(FRONTEND_DIST.resolve()):
        raise HTTPException(status_code=404, detail="Not found")
    if asset.is_file():
        return FileResponse(asset)
    if path.startswith("assets/") or Path(path).suffix:
        raise HTTPException(status_code=404, detail="Asset not found")
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=503, detail='Build the frontend first: cd "front end" and npm run build. For development, run npm run dev separately.')
    return FileResponse(index)
