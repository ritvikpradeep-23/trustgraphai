"""GET /health: is the server up. Loads nothing heavy."""
from fastapi import APIRouter

from app.schemas import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut()
