"""GET /health: is the server up, and what is configured. Loads nothing heavy."""
from fastapi import APIRouter, Request

from app.schemas import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health(request: Request) -> HealthOut:
    service = request.app.state.scam_service
    return HealthOut(reports_stored=service.repository.count(), embedding_model_loaded=service.embedder.is_loaded,
                     deepfake_model=request.app.state.deepfake_status,
                     deepfake_mode=request.app.state.settings.deepfake_mode)
