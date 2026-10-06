"""Real inference probe, independent of database matching and user messages."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.ai.scam_engine import analyze

router = APIRouter(tags=["Health"])


@router.get("/health/scam-model")
def scam_model_health():
    # Loading the joblib file alone does not prove the whole pipeline can run.
    result = analyze("The volunteer meeting has moved to Wednesday afternoon.")
    if result is None:
        return JSONResponse(status_code=503, content={
            "ok": False, "model": "original-scam-engine", "inference": "unavailable"})
    return {"ok": True, "model": "original-scam-engine", "inference": "verified",
            "signals": sorted(result["signals"]), "score_kind": "review-score"}
