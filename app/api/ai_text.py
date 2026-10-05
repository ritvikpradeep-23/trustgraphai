"""POST /api/text/ai-check: does this text read as AI-written?

Separate from the scam check on purpose: AI-written is not the same as a scam,
and a person can send a scam they typed themselves.
"""
from fastapi import APIRouter, Request

from app.ai_text_engine import check
from app.errors import ApiError
from app.schemas import AiCheckIn, AiCheckOut, ErrorOut

router = APIRouter(prefix="/api/text", tags=["text"])


@router.post("/ai-check", response_model=AiCheckOut, responses={422: {"model": ErrorOut}, 503: {"model": ErrorOut}})
def ai_check(body: AiCheckIn, request: Request) -> dict:
    state = request.app.state
    if state.ai_text_detector is None:
        raise ApiError(503, "model_not_configured", "train the AI-text model first: python train_text.py")
    if len(body.text) > state.settings.max_text_chars:
        raise ApiError(422, "text_too_long", f"at most {state.settings.max_text_chars} characters")
    return check(state.ai_text_detector, body.text, state.settings)
