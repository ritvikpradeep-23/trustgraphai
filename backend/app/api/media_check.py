"""/api/score with "type": "image" or "video" (sent by the extension's
click-to-check on any website).

Request:  {type: "image", payload: <data: URL>, hostname, timestamp, capture}
          {type: "video", payload: [{t: <seconds>, data: <data: URL>}, ...], ...}
Response: {type, hostname, frames, deepfake: <the existing model's verdict,
          or {result: "not_checked", reason}>, fingerprint: {db_match,
          similarity, matched_record_id, ...}}

The model's answer and the database match are separate fields: the match is
never blended into the model score. Images are decoded in memory only.
"""
import logging

import numpy as np
from fastapi import Request

from app.deepfake_engine.service import analyze_frames
from app.errors import ApiError
from app.fingerprint import service as fp
from app.fingerprint.hashing import BadImage, decode_image

logger = logging.getLogger("trustgraph.media")
MEDIA_TYPES = ("image", "video")


def _frames(body: dict, settings) -> tuple[list, list]:
    payload = body.get("payload")
    if body["type"] == "image":
        items = [{"t": 0, "data": payload}]
    else:
        if not isinstance(payload, list) or not payload:
            raise ApiError(422, "invalid_request", "payload: a video needs a list of {t, data} frames")
        if len(payload) > settings.media_max_frames:
            raise ApiError(413, "too_many_frames", f"at most {settings.media_max_frames} frames")
        items = payload
    images, times = [], []
    for item in items:
        data = item.get("data") if isinstance(item, dict) else None
        try:
            images.append(decode_image(data, settings.media_max_image_bytes))
        except BadImage as exc:
            raise ApiError(422, "bad_image", str(exc)) from exc
        t = item.get("t") if isinstance(item, dict) else None
        times.append(t if isinstance(t, (int, float)) else None)
    return images, times


def check_media(request: Request, body: dict) -> dict:
    state, settings = request.app.state, request.app.state.settings
    if int(request.headers.get("content-length") or 0) > settings.media_max_body:
        raise ApiError(413, "too_large", f"request body over {settings.media_max_body} bytes")
    images, times = _frames(body, settings)

    # The existing deepfake model, unchanged. Without one we say so; we never make up a score.
    if state.deepfake_model is None:
        deepfake = {"result": "not_checked", "reason": f"no deepfake model configured ({state.deepfake_status})"}
    else:
        bgr = [np.asarray(img)[:, :, ::-1].copy() for img in images]
        deepfake = analyze_frames(bgr, state.deepfake_model, state.face_detector, settings)

    store = state.fingerprint_store
    if store is None:
        fingerprint = {**fp.NO_MATCH, "available": False, "reason": state.fingerprint_status}
    else:
        try:
            fingerprint = (fp.check_image(store, images[0], settings) if body["type"] == "image"
                           else fp.check_frames(store, images, settings))
        except Exception as exc:  # the database must never hide the model's answer
            logger.warning("media fingerprint lookup failed: %s", exc)
            fingerprint = {**fp.NO_MATCH, "available": False, "reason": "lookup failed"}

    logger.info("media check: %s, %d frame(s), host=%s, model=%s, db_match=%s", body["type"], len(images),
                str(body.get("hostname") or "")[:100], deepfake.get("result"), fingerprint["db_match"])
    return {"type": body["type"], "hostname": str(body.get("hostname") or "")[:253], "frames": len(images),
            "frame_times": times, "deepfake": deepfake, "fingerprint": fingerprint}


def text_fingerprint(request: Request, text) -> dict:
    """The database match for /api/score text checks (a separate field)."""
    store = request.app.state.fingerprint_store
    if store is None:
        return {**fp.NO_MATCH, "available": False, "reason": request.app.state.fingerprint_status}
    if not isinstance(text, str) or not text.strip():
        return dict(fp.NO_MATCH)
    try:
        return fp.check_text(store, text[:request.app.state.settings.max_text_chars], request.app.state.settings)
    except Exception as exc:  # the database must never break the scam score
        logger.warning("text fingerprint lookup failed: %s", exc)
        return {**fp.NO_MATCH, "available": False, "reason": "lookup failed"}
