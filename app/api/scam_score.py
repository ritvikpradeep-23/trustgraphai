"""The scam check the browser extension uses, now inside the API.

  GET  /               the TrustGraph test page (same page as run_website.py)
  GET  /api/examples   example interactions for that page
  POST /api/score      {message_text, channel, ...} -> {band, score, explanation, signals}

Same answers as run_website.py, so the extension (backend_url
http://127.0.0.1:8000) works with either server. When the AI-text model is
trained, the answer also has "ai_written": {result, ai_score}; older extension
versions ignore fields they don't know.
"""
from fastapi import APIRouter, Body, Request
from fastapi.responses import HTMLResponse

from app.ai_text_engine import check
from app.errors import ApiError

router = APIRouter(tags=["scam check"])
MAX_BODY = 200_000  # same limit as run_website.py


def _web():
    from trustgraph.web import server  # the 4-signal engine; imported late so the API starts fast
    return server


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def page() -> HTMLResponse:
    return HTMLResponse(_web().PAGE)


@router.get("/api/examples")
def examples() -> list[dict]:
    return _web()._examples()


@router.post("/api/score")
def score(request: Request, interaction: dict = Body(...)) -> dict:
    if int(request.headers.get("content-length") or 0) > MAX_BODY:
        raise ApiError(413, "too_large", f"request body over {MAX_BODY} bytes")
    result = _web().score(interaction)
    detector = request.app.state.ai_text_detector
    text = interaction.get("message_text")
    if detector is not None and isinstance(text, str) and text.strip():
        result["ai_written"] = check(detector, text[:request.app.state.settings.max_text_chars],
                                     request.app.state.settings)
    return result
