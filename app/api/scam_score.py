"""The scam check the browser extension uses, now inside the API.

  GET  /               the TrustGraph test page (same page as run_website.py)
  GET  /api/examples   example interactions for that page
  POST /api/score      {message_text, channel, ...} -> {band, score, explanation, signals}

Same answers as run_website.py, so the extension (backend_url
http://127.0.0.1:8000) works with either server. When the AI-text model is
trained, the answer also has "ai_written": {result, ai_score}; older extension
versions ignore fields they don't know.

Also (additive): every text answer has "fingerprint": {db_match, similarity,
matched_record_id}, the match against the known-fakes database, next to the
score and never blended into it. A body with "type": "image" or "video" is a
media check from the extension's click-to-check (app/api/media_check.py).
"""
from fastapi import APIRouter, Body, Request
from fastapi.responses import HTMLResponse

from app.ai_text_engine import check
from app.api.media_check import MEDIA_TYPES, check_media, text_fingerprint
from app.errors import ApiError

router = APIRouter(tags=["scam check"])
MAX_BODY = 200_000  # same limit as run_website.py
# Fields the universal click-to-check adds; kept out of the scoring input.
CHECK_FIELDS = ("type", "payload", "hostname", "timestamp", "capture")


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
    if interaction.get("type") in MEDIA_TYPES:
        return check_media(request, interaction)
    if int(request.headers.get("content-length") or 0) > MAX_BODY:
        raise ApiError(413, "too_large", f"request body over {MAX_BODY} bytes")
    if interaction.get("type") == "text" and not interaction.get("message_text") and isinstance(interaction.get("payload"), str):
        interaction["message_text"] = interaction["payload"]
    fingerprint_text = interaction.get("message_text")
    interaction = {k: v for k, v in interaction.items() if k not in CHECK_FIELDS}
    result = _web().score(interaction)
    detector = request.app.state.ai_text_detector
    text = interaction.get("message_text")
    if detector is not None and isinstance(text, str) and text.strip():
        result["ai_written"] = check(detector, text[:request.app.state.settings.max_text_chars],
                                     request.app.state.settings)
    result["fingerprint"] = text_fingerprint(request, fingerprint_text)
    return result
