"""Extension <-> workspace integration: pairing, verdict-only Result sync,
feedback, heartbeat, and the workspace views that show them.

Needs a real PostgreSQL in TEST_DATABASE_URL (skipped otherwise); each test
runs inside a transaction that is rolled back.
"""
import os
import time
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def result(rid="0f8c2a6e-1d2b-4c3d-9e8f-123456789abc", **extra):
    return {"id": rid, "timestamp": time.time() * 1000, "riskLevel": "high", "score": 92,
            "signalIds": ["money_request", "impersonation"], "channel": "whatsapp", "domain": "web.whatsapp.com", **extra}


@unittest.skipUnless(TEST_DATABASE_URL, "set TEST_DATABASE_URL to a PostgreSQL database to run")
class ExtensionSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(TEST_DATABASE_URL)
        Base.metadata.create_all(cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.conn = self.engine.connect()
        self.trans = self.conn.begin()
        self.db = Session(bind=self.conn, join_transaction_mode="create_savepoint")

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.trans.rollback()
        self.conn.close()

    def pair(self):
        code = self.client.post("/api/extension/pairing-code").json()["code"]
        r = self.client.post("/api/extension/pair", json={"code": code.lower()})
        self.assertEqual(r.status_code, 200, r.text)
        return {"Authorization": "Bearer " + r.json()["token"]}, code

    def test_pairing_code_works_once(self):
        _, code = self.pair()
        self.assertRegex(code, r"^[A-Z0-9]{4}-[A-Z0-9]{4}$")
        self.assertEqual(self.client.post("/api/extension/pair", json={"code": code}).status_code, 400)
        self.assertEqual(self.client.post("/api/extension/pair", json={"code": "NOPE-0000"}).status_code, 400)

    def test_results_need_a_token(self):
        self.assertEqual(self.client.post("/api/results", json=result()).status_code, 401)
        self.assertEqual(self.client.get("/api/results", headers={"Authorization": "Bearer wrong"}).status_code, 401)

    def test_sync_list_delete(self):
        auth, _ = self.pair()
        self.assertEqual(self.client.post("/api/results", json=result(), headers=auth).status_code, 201)
        self.assertEqual(self.client.post("/api/results", json=result(score=95), headers=auth).status_code, 201)  # update, no duplicate
        listed = self.client.get("/api/results", headers=auth).json()
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["score"], 95)
        self.assertEqual(set(listed[0]), {"id", "timestamp", "riskLevel", "score", "signalIds", "channel", "domain"})
        self.assertEqual(self.client.get("/api/export", headers=auth).json(), listed)
        self.client.delete(f"/api/results/{listed[0]['id']}", headers=auth)
        self.assertEqual(self.client.get("/api/results", headers=auth).json(), [])

    def test_text_can_never_be_stored(self):
        auth, _ = self.pair()
        for bad in (result(text="Share the OTP now"), result(signalIds=["Share OTP 482913 now"]),
                    result(channel="Dear customer"), result(domain="x.com/path?msg=hi"), result(score=101)):
            self.assertEqual(self.client.post("/api/results", json=bad, headers=auth).status_code, 422, bad)

    def test_another_extension_cannot_touch_my_results(self):
        mine, _ = self.pair()
        theirs, _ = self.pair()
        self.client.post("/api/results", json=result(), headers=mine)
        self.assertEqual(self.client.get("/api/results", headers=theirs).json(), [])
        self.assertEqual(self.client.post("/api/results", json=result(), headers=theirs).status_code, 409)
        self.client.delete("/api/results", headers=theirs)
        self.assertEqual(len(self.client.get("/api/results", headers=mine).json()), 1)

    def test_workspace_shows_synced_verdicts_and_feedback(self):
        auth, _ = self.pair()
        rid = result()["id"]
        self.client.post("/api/results", json=result(), headers=auth)
        items = self.client.get("/api/workspace/detections").json()
        mine = next(i for i in items if i["id"] == rid)
        self.assertEqual((mine["riskLevel"], mine["riskScore"], mine["channel"], mine["site"]), ("HIGH", 0.92, "whatsapp", "web.whatsapp.com"))
        self.assertIn("request for money", mine["explanation"])
        self.assertEqual(mine["engineVersion"], "browser-extension")
        self.client.post("/api/feedback", json={"resultId": rid})
        self.assertEqual(self.client.get(f"/api/workspace/detections/{rid}").json()["feedback"], "false_alarm")

    def test_heartbeat_drives_workspace_status(self):
        self.client.post("/api/status", json={"source": "whatsapp", "ts": 1})
        status = self.client.get("/api/workspace/status").json()
        self.assertEqual(status["state"], "CONNECTED")
        self.assertIsNotNone(status["lastSeen"])


if __name__ == "__main__":
    unittest.main()
