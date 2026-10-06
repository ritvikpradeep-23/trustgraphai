from fastapi import FastAPI

from app.api.ai_detectors import router as ai_detectors_router
from app.api.database_health import router as database_health_router
from app.api.detect import router as detect_router
from app.api.detection_history import router as detection_history_router
from app.api.media_check import router as media_check_router
from app.api.report import router as report_router
from app.api.relationships import router as relationships_router
from app.api.provenance import router as provenance_router
from app.api.submission import router as submission_router
from app.api.url_analysis import router as url_analysis_router
from app.core.database import create_tables


app = FastAPI(
    title="TrustGraph API",
    description="TrustGraph scam detection backend",
    version="0.1.0",
)

app.include_router(detect_router, prefix="/api")
app.include_router(detection_history_router, prefix="/api")
app.include_router(report_router, prefix="/api")
app.include_router(submission_router, prefix="/api")
app.include_router(ai_detectors_router, prefix="/api")
app.include_router(provenance_router, prefix="/api")
app.include_router(url_analysis_router, prefix="/api")
app.include_router(relationships_router, prefix="/api")
app.include_router(media_check_router, prefix="/api")
app.include_router(database_health_router)


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.get("/health")
def health():
    return {"status": "ok"}
