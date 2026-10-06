from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.url_analysis import analyze_url


router = APIRouter(tags=["URL Analysis"])


class URLAnalyzeRequest(BaseModel):
    url: str = Field(min_length=1, max_length=4096)


class URLAnalyzeResponse(BaseModel):
    normalized_url: str
    scheme: str
    hostname: str
    registrable_domain: str
    port: int | None
    path: str
    query: str
    signals: dict[str, bool]
    reasons: list[str]


@router.post("/url/analyze", response_model=URLAnalyzeResponse)
def url_analyze(request: URLAnalyzeRequest):
    try:
        return analyze_url(request.url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
