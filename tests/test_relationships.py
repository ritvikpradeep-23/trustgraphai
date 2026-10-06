import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.relationships import get_db
from app.main import app
from app.services.correlation import validate_relationship


class FakeSession:
    def __init__(self):
        self.submissions = {
            "s1": SimpleNamespace(submission_id="s1", sender="alice", url="https://shop.example.com/a", text="same reported scam text that is long enough", caption=None),
            "s2": SimpleNamespace(submission_id="s2", sender="ALICE", url="https://shop.example.com/a", text="same reported scam text that is long enough", caption=None),
        }
        self.records = []

    def get(self, model, key):
        return self.submissions.get(key)

    def scalar(self, _statement):
        return self.records[0] if self.records else None

    def scalars(self, _statement):
        return SimpleNamespace(all=lambda: list(self.records))

    def add(self, record):
        self.records.append(record)

    def commit(self):
        pass

    def refresh(self, _record):
        pass

    def rollback(self):
        pass


class RelationshipTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeSession()

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_relationships_require_deterministic_evidence(self):
        evidence = validate_relationship(self.db, "same_sender", "submission", "s1", "submission", "s2")
        self.assertEqual(evidence["sender"], "alice")
        with self.assertRaises(LookupError):
            validate_relationship(self.db, "same_sender", "submission", "s1", "submission", "missing")

    def test_create_relationship_is_idempotent_and_order_independent(self):
        first = self.client.post("/api/relationships", json={
            "relationship_type": "same_reported_content",
            "source_entity_type": "submission", "source_entity_id": "s1",
            "target_entity_type": "submission", "target_entity_id": "s2",
        })
        second = self.client.post("/api/relationships", json={
            "relationship_type": "same_reported_content",
            "source_entity_type": "submission", "source_entity_id": "s2",
            "target_entity_type": "submission", "target_entity_id": "s1",
        })
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(first.json()["relationship_id"], second.json()["relationship_id"])
        self.assertEqual(len(self.db.records), 1)
        retrieved = self.client.get("/api/relationships")
        self.assertEqual(retrieved.status_code, 200)
        self.assertEqual(len(retrieved.json()), 1)

    def test_route_rejects_relationship_not_supported_by_stored_data(self):
        with patch("app.api.relationships.validate_relationship", side_effect=ValueError("no match")):
            response = self.client.post("/api/relationships", json={
                "relationship_type": "same_url_domain",
                "source_entity_type": "submission", "source_entity_id": "s1",
                "target_entity_type": "submission", "target_entity_id": "s2",
            })
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.db.records, [])


if __name__ == "__main__":
    unittest.main()
