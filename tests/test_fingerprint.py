"""Known-fakes fingerprints and the extension's database connection.

Hashing tests need nothing. Database tests need a real PostgreSQL in
TEST_DATABASE_URL (they are skipped otherwise); each runs inside a
transaction that is rolled back, so the database is left untouched:

    TEST_DATABASE_URL=postgresql+psycopg://postgres:<password>@127.0.0.1:5432/trustgraph_test \
        python -m unittest tests.test_fingerprint -v
"""
import base64
import importlib.util
import io
import os
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.database import Base, get_db
from app.fingerprint import hashing, store
from app.fingerprint import service as fp
from app.main import app

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("seed_fingerprints", ROOT / "scripts/seed_fingerprints.py")
seed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seed)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
KNOWN_TEXT = seed.DEMO_TEXTS[0]
UNRELATED_TEXT = "Lunch at the canteen at one? I will bring the notes for the exam tomorrow."


def recompressed(img: Image.Image) -> Image.Image:
    """What a messaging app does to a shared image: smaller, heavy JPEG."""
    small = img.resize((int(img.width * 0.85), int(img.height * 0.85)), Image.Resampling.BILINEAR)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=30)
    return Image.open(io.BytesIO(buf.getvalue())).convert("RGB")


def data_url(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


class HashingTests(unittest.TestCase):
    def test_hashes_survive_recompression(self):
        known, unrelated = seed.demo_image(seed=7), seed.demo_image(seed=99)
        copy = recompressed(known)
        self.assertLessEqual(hashing.hamming(hashing.phash(known), hashing.phash(copy)), 10)
        self.assertLessEqual(hashing.hamming(hashing.dhash(known), hashing.dhash(copy)), 10)
        self.assertGreater(hashing.hamming(hashing.phash(known), hashing.phash(unrelated)), 10)

    def test_bad_payloads_are_rejected(self):
        with self.assertRaises(hashing.BadImage):
            hashing.decode_image("not an image", 1000)
        with self.assertRaises(hashing.BadImage):
            hashing.decode_image(data_url(seed.demo_image()), 100)  # over the size limit

    def test_signed_round_trip_for_postgres_bigint(self):
        for value in (0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1):
            self.assertEqual(hashing.to_unsigned(hashing.to_signed(value)), value)
            self.assertTrue(-(1 << 63) <= hashing.to_signed(value) < (1 << 63))


@unittest.skipUnless(TEST_DATABASE_URL, "set TEST_DATABASE_URL to a PostgreSQL database to run")
class DatabaseTests(unittest.TestCase):
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
        self.known, self.unrelated = seed.demo_image(seed=7), seed.demo_image(seed=99)
        self.record_id = fp.add_image(self.db, self.known, "known-fake", "test")
        seed.add_reported_text(self.db, KNOWN_TEXT)

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        self.trans.rollback()
        self.conn.close()

    # --- store -------------------------------------------------------------
    def test_lookup_matches_copies_not_unrelated(self):
        exact = fp.check_image(self.db, self.known)
        copy = fp.check_image(self.db, recompressed(self.known))
        other = fp.check_image(self.db, self.unrelated)
        self.assertTrue(exact["db_match"])
        self.assertEqual(exact["similarity"], 1.0)
        self.assertTrue(copy["db_match"])
        self.assertEqual(copy["matched_record_id"], self.record_id)
        self.assertFalse(other["db_match"])

    def test_band_index_finds_close_records_without_full_scan(self):
        h = hashing.phash(self.known)
        found = store.lookup(self.db, "image", h ^ 0b101, threshold=10, full_scan_max=0)  # index only
        self.assertEqual(found["matched_record_id"], self.record_id)
        # Each band has its own (kind, band) index. Which one the planner picks
        # on a tiny test table varies, so check the indexes exist rather than
        # assert one particular plan.
        indexes = {r[0] for r in self.db.execute(text(
            "SELECT indexname FROM pg_indexes WHERE tablename = 'fingerprints'"))}
        self.assertTrue({f"ix_fingerprints_b{i}" for i in range(4)} <= indexes, indexes)

    # --- POST /api/media/check ------------------------------------------------
    def check(self, img):
        r = self.client.post("/api/media/check", json={"type": "image", "payload": data_url(img), "hostname": "example.com",
                                                       "timestamp": 1760000000000, "capture": "direct"})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_media_check_image(self):
        seeded, copy, other = self.check(self.known), self.check(recompressed(self.known)), self.check(self.unrelated)
        self.assertTrue(seeded["fingerprint"]["db_match"])
        self.assertTrue(copy["fingerprint"]["db_match"])
        self.assertEqual(copy["fingerprint"]["matched_record_id"], self.record_id)
        self.assertFalse(other["fingerprint"]["db_match"])
        # No model is connected: the answer says so instead of making up a score.
        self.assertEqual(seeded["deepfake"]["result"], "not_checked")
        self.assertFalse(seeded["deepfake"]["available"])

    def test_media_check_video_frames(self):
        frames = [{"t": 0.0, "data": data_url(self.unrelated)}, {"t": 0.5, "data": data_url(recompressed(self.known))}]
        body = self.client.post("/api/media/check", json={"type": "video", "payload": frames}).json()
        self.assertEqual(body["frames"], 2)
        self.assertEqual(body["frame_times"], [0.0, 0.5])
        self.assertTrue(body["fingerprint"]["db_match"])
        self.assertEqual(body["fingerprint"]["frames_matched"], 1)

    def test_media_check_rejects_bad_input(self):
        self.assertEqual(self.client.post("/api/media/check", json={"type": "image", "payload": "nope"}).status_code, 422)
        self.assertEqual(self.client.post("/api/media/check", json={"type": "video", "payload": []}).status_code, 422)
        self.assertEqual(self.client.post("/api/media/check", json={"type": "audio", "payload": "x"}).status_code, 422)

    # --- the extension's text check: POST /api/detect pattern matching ---------
    def test_detect_matches_reported_scams(self):
        retyped = "DEAR CUSTOMER!! Your SBI KYC is pending, and your account will be blocked today... share the OTP to verify immediately"
        hit = self.client.post("/api/detect", json={"channel": "whatsapp", "text": retyped}).json()
        miss = self.client.post("/api/detect", json={"channel": "whatsapp", "text": UNRELATED_TEXT}).json()
        self.assertTrue(hit["previous_report_matches"])
        self.assertGreaterEqual(hit["previous_report_matches"][0]["similarity_score"], 0.72)
        self.assertEqual(miss["previous_report_matches"], [])

    # --- GET /health/database -------------------------------------------------
    def test_health_round_trip_leaves_nothing_behind(self):
        before = store.count(self.db)
        body = self.client.get("/health/database").json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["probe_found"])
        self.assertGreaterEqual(body["reports"], 1)
        self.assertEqual(store.count(self.db), before)


if __name__ == "__main__":
    unittest.main()
