import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from trustgraph.web.server import Handler, score


@pytest.fixture(scope="module")
def base_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def _post(url, body: bytes):
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


def test_page_and_examples_are_served(base_url):
    with urllib.request.urlopen(base_url + "/") as res:
        assert b"TrustGraph Tester" in res.read()
    with urllib.request.urlopen(base_url + "/api/examples") as res:
        examples = json.loads(res.read())
    assert {ex["kind"] for ex in examples} == {"scam", "legit"}


def test_scoring_returns_band_and_every_signal(base_url):
    status, data = _post(base_url + "/api/score", json.dumps(
        {"message_text": "This is your bank's fraud team, move your savings to a safe account today."}).encode())
    assert status == 200
    assert data["band"] in {"Low", "Caution", "High"}
    assert {s["name"] for s in data["signals"]} == {"anomaly", "continuity", "similarity", "precedent"}


@pytest.mark.parametrize("body", [b"not json", b"[1, 2]"])
def test_bad_requests_are_rejected(base_url, body):
    status, data = _post(base_url + "/api/score", body)
    assert status == 400
    assert "error" in data


def test_urgency_is_counted_from_the_message_when_blank():
    result = score({"message_text": "Pay today, it's urgent, do it immediately"})
    assert result["urgency_counted"] == 3
    assert score({"message_text": "urgent", "urgency_score": 0})["urgency_counted"] is None
