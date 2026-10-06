from fastapi import APIRouter, File, UploadFile

from app.schemas.detection import (
    AIWrittenCheckRequest,
    ModalityCheckResponse,
    VideoAnalyzeResponse,
)
from app.services.ai_model import TrustGraphAI


router = APIRouter(tags=["AI Detectors"])
ai_service = TrustGraphAI()


@router.post("/video/analyze", response_model=VideoAnalyzeResponse)
def analyze_video(file: UploadFile = File(...)):
    result = ai_service.analyze("video", {"file": file.file, "filename": file.filename})
    return VideoAnalyzeResponse(
        fake_score=None,
        available=result.available,
        model=result.model,
        reasons=result.reasons,
    )


@router.post("/text/ai-check", response_model=ModalityCheckResponse)
def check_ai_written_text(request: AIWrittenCheckRequest):
    result = ai_service.analyze("ai_content", {"text": request.text})
    return ModalityCheckResponse(
        ai_written_score=None,
        available=result.available,
        model=result.model,
        reasons=result.reasons,
    )
