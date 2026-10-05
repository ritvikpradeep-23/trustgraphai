"""POST /api/feedback: "this is a scam" or "this was wrongly flagged".

The message goes into the learning inbox (data/learning/inbox.jsonl, on this
computer only), and the next hourly learning run (learn_cycle.py) tests the
engine on it once and learns from it if it was missed. The text is never sent
back by any endpoint and never written to the server log.
"""
import logging

from fastapi import APIRouter, Request

from app.errors import ApiError
from app.schemas import ErrorOut, FeedbackIn, FeedbackOut

router = APIRouter(tags=["learning"])
logger = logging.getLogger("trustgraph.feedback")


@router.post("/api/feedback", response_model=FeedbackOut, status_code=201, responses={422: {"model": ErrorOut}})
def feedback(body: FeedbackIn, request: Request) -> FeedbackOut:
    if len(body.text) > request.app.state.settings.max_text_chars:
        raise ApiError(422, "text_too_long", f"at most {request.app.state.settings.max_text_chars} characters")
    from add_examples import add
    add(body.text, body.label, body.scam_type, source=f"api ({body.source})")
    logger.info("feedback queued label=%s source=%s chars=%d", body.label, body.source, len(body.text))
    return FeedbackOut()
