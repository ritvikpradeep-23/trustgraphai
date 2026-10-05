"""POST /api/text/report and POST /api/text/analyze.

Endpoints are plain `def` (not async): embedding is CPU work, and FastAPI runs
`def` endpoints in a thread pool so one slow request doesn't block the others.
"""
import logging
from contextlib import contextmanager

from fastapi import APIRouter, Request

from app.errors import ApiError
from app.schemas import AnalyzeOut, ErrorOut, ReportOut, TextIn
from app.scam_engine.embedder import EmbeddingUnavailable
from app.scam_engine.service import ScamService, normalize_text

router = APIRouter(prefix="/api/text", tags=["text"])
logger = logging.getLogger("trustgraph.text")


@contextmanager
def _model_errors():
    """A missing embedding model is a server-side setup problem: say so with
    a 503 instead of a generic 500."""
    try:
        yield
    except EmbeddingUnavailable as exc:
        logger.error("%s", exc)
        raise ApiError(503, "embedding_model_unavailable", str(exc)) from exc


def _checked(body: TextIn, request: Request) -> ScamService:
    settings = request.app.state.settings
    if len(body.text) > settings.max_text_chars:
        raise ApiError(413, "text_too_long", f"at most {settings.max_text_chars} characters")
    if not normalize_text(body.text):
        raise ApiError(422, "empty_text", "text has no visible characters")
    return request.app.state.scam_service


@router.post("/report", response_model=ReportOut, status_code=201,
             responses={413: {"model": ErrorOut}, 422: {"model": ErrorOut}, 503: {"model": ErrorOut}})
def report(body: TextIn, request: Request) -> ReportOut:
    with _model_errors():
        report_id = _checked(body, request).report(body.text, body.source)
    # Log the id, length and source only: message text can contain personal details.
    logger.info("report stored id=%s source=%s chars=%d", report_id, body.source, len(body.text))
    return ReportOut(id=report_id)


@router.post("/analyze", response_model=AnalyzeOut,
             responses={413: {"model": ErrorOut}, 422: {"model": ErrorOut}, 503: {"model": ErrorOut}})
def analyze(body: TextIn, request: Request) -> AnalyzeOut:
    with _model_errors():
        result = _checked(body, request).analyze(body.text)
    logger.info("analyze source=%s chars=%d risk=%s", body.source, len(body.text), result.risk_level)
    return result
