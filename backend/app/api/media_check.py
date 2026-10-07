"""POST /api/media/check: an image or video frames captured by the browser
extension's click-to-check on any website.

Request:  {type: "image", payload: <data: URL>, hostname, timestamp, capture}
          {type: "video", payload: [{t: <seconds>, data: <data: URL>}, ...], ...}
Response: {type, hostname, frames, frame_times, capture,
           fingerprint: {db_match, similarity, matched_record_id, ...}}

A match against the known-fakes fingerprint database only; no deepfake model
is used. Images are decoded in memory only and never stored.
"""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.fingerprint import config
from app.fingerprint import service as fp
from app.fingerprint.hashing import BadImage, decode_image
from app.fingerprint.store import NO_MATCH

router = APIRouter(tags=["Media check"])
logger = logging.getLogger("trustgraph.media")


class MediaFrame(BaseModel):
    t: float | None = None
    data: str


class MediaCheckRequest(BaseModel):
    type: Literal["image", "video"]
    payload: str | list[MediaFrame]
    hostname: str | None = None
    timestamp: int | None = None
    capture: str | None = None


@router.post("/media/check")
def media_check(body: MediaCheckRequest, request: Request, db: Session = Depends(get_db)) -> dict:
    if int(request.headers.get("content-length") or 0) > config.MEDIA_MAX_BODY:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"request body over {config.MEDIA_MAX_BODY} bytes")
    if body.type == "image":
        if not isinstance(body.payload, str):
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "an image payload is one data: URL")
        frames = [MediaFrame(t=0, data=body.payload)]
    else:
        if not isinstance(body.payload, list) or not body.payload:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "a video needs a list of {t, data} frames")
        if len(body.payload) > config.MEDIA_MAX_FRAMES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"at most {config.MEDIA_MAX_FRAMES} frames")
        frames = body.payload
    try:
        images = [decode_image(f.data, config.MEDIA_MAX_IMAGE_BYTES) for f in frames]
    except BadImage as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    try:
        fingerprint = fp.check_image(db, images[0]) if body.type == "image" else fp.check_frames(db, images)
    except Exception as exc:  # the database must never hide the rest of the answer
        logger.warning("fingerprint lookup failed: %s", exc)
        db.rollback()
        fingerprint = {**NO_MATCH, "available": False, "reason": "database lookup failed"}

    logger.info("media check: %s, %d frame(s), host=%s, db_match=%s", body.type, len(images),
                (body.hostname or "")[:100], fingerprint["db_match"])
    return {"type": body.type, "hostname": (body.hostname or "")[:253], "frames": len(images),
            "frame_times": [f.t for f in frames], "capture": body.capture,
            "fingerprint": fingerprint}
