"""GET /health/fingerprint: proves backend -> database round trip.

Writes a probe fingerprint, looks it up, and rolls it back (nothing is left
behind). The extension calls this to confirm extension -> backend -> DB.
"""
from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/health/fingerprint")
def fingerprint_health(request: Request) -> dict:
    store = request.app.state.fingerprint_store
    if store is None:
        return {"ok": False, "database": "unavailable", "reason": request.app.state.fingerprint_status}
    try:
        result = store.self_test()
    except Exception as exc:
        return {"ok": False, "database": "error", "reason": str(exc)[:200]}
    return {**result, "database": "sqlite", "image_records": store.count("image"), "text_records": store.count("text")}
