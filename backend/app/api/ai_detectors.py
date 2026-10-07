from fastapi import APIRouter

from app.schemas.detection import (
    AIWrittenCheckRequest,
    ModalityCheckResponse,
)
from app.services.ai_model import TrustGraphAI


router = APIRouter(tags=["AI Detectors"])
ai_service = TrustGraphAI()


@router.post("/text/ai-check", response_model=ModalityCheckResponse)
def check_ai_written_text(request: AIWrittenCheckRequest):
    result = ai_service.analyze("ai_content", {"text": request.text})
    return ModalityCheckResponse(
        ai_written_score=result.risk_score,  # None unless a trained engine answered
        available=result.available,
        model=result.model,
        reasons=result.reasons,
    )
