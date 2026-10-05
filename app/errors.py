"""One error type for the whole API, so every error reply has the same shape:
{"error": "<short_code>", "detail": "<optional human text>"}."""


class ApiError(Exception):
    def __init__(self, status_code: int, error: str, detail: str | None = None):
        self.status_code, self.error, self.detail = status_code, error, detail
