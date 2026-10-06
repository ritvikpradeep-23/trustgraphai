"""Local test website: type in an interaction, see how TrustGraph scores it.

Standard library only. Binds to 127.0.0.1, so nothing is reachable from
other machines.

    python run_website.py        (from the repository root)
"""
import json
import math
import re
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from trustgraph.fusion import risk_band
from trustgraph.pipeline import score_interaction
from trustgraph.scenarios import SCENARIOS

HOST, PORT = "127.0.0.1", 8000
MAX_BODY = 200_000
PAGE = (Path(__file__).parent / "index.html").read_bytes()

# The anomaly signal's urgency_score is "urgency keywords in the content
# text"; when the form leaves it blank, count them from the message.
_URGENCY = re.compile(
    r"\b(urgent(ly)?|immediately|right now|asap|today|tonight|quickly|hurry|final (notice|warning)|"
    r"act now|within (24|48) hours|before it'?s too late|as soon as possible)\b", re.IGNORECASE)


def _json_safe(value):
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    return value


def _examples() -> list[dict]:
    return [{"name": name, "kind": kind, "interaction": _json_safe(interaction)}
            for name, kind, interaction in SCENARIOS]


def score(interaction: dict) -> dict:
    urgency_counted = False
    if interaction.get("urgency_score") is None and isinstance(interaction.get("message_text"), str):
        interaction["urgency_score"] = len(_URGENCY.findall(interaction["message_text"]))
        urgency_counted = True
    signals, fused = score_interaction(interaction)
    return {
        "band": risk_band(fused.score),
        "score": fused.score,
        "explanation": fused.explanation,
        "urgency_counted": interaction["urgency_score"] if urgency_counted else None,
        "signals": [{"name": s.signal_name, "score": s.score, "explanation": s.explanation} for s in signals],
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload):
        self._send(status, json.dumps(payload).encode(), "application/json")

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path == "/api/examples":
            self._json(200, _examples())
        elif self.path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/score":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length") or 0)
        if not 0 < length <= MAX_BODY:
            return self._json(400, {"error": "request body missing or too large"})
        try:
            interaction = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return self._json(400, {"error": "body must be JSON"})
        if not isinstance(interaction, dict):
            return self._json(400, {"error": "body must be a JSON object"})
        self._json(200, score(interaction))

    def log_message(self, fmt, *args):
        pass


def main(open_browser: bool = True):
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"TrustGraph test site running at {url}  (press Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
