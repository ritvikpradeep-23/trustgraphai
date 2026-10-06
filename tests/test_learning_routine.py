"""The hourly new-scam learning routine (learn_cycle.py), add_examples.py and
POST /api/feedback. Uses the real engine and dev rounds; the full test suite
inside the gate is replaced by a stub (it would run these tests again)."""
import json

import pytest
from fastapi.testclient import TestClient

import add_examples
import install_schedule
import learn_cycle
from app.config import Settings
from app.main import create_app
from routine import core

NEW = [("scam", "Your gas connection will be blocked today due to pending e-KYC. Update now at gas-kyc-update.in",
        "LPG e-KYC block"),
       ("scam", "LPG subsidy stopped! Complete your e-KYC within 2 hours at lpg-ekyc.co or connection cancelled",
        "LPG e-KYC block"),
       ("scam", "Your SIM will stop working in 24 hours. To upgrade to 5G send the OTP you receive", "5G SIM upgrade"),
       ("scam", "Hey it's me, lost my phone, new number. Send 4000 on GPay urgently, will return tomorrow", None),
       ("honest", "Your LPG cylinder booking is confirmed. Delivery expected on Thursday.", None),
       ("honest", "Hey, it's Priya, new number! Save this one. See you at the wedding on Sunday", None)]


@pytest.fixture
def learn(tmp_path, monkeypatch):
    """Every file the routine writes goes to tmp_path; the gate's test run and SMS file are stubbed."""
    d = tmp_path / "learning"
    for name, path in {"LEARN_DIR": d, "INBOX": d / "inbox.jsonl", "USED": d / "used.json",
                       "REJECTED": d / "rejected.jsonl", "SCAM_REPORTS": tmp_path / "scam_reports.json",
                       "BEST": tmp_path / "learning_best.json", "OUT": tmp_path / "reports",
                       "DATASETS": d / "datasets", "GENERATED": d / "generated", "STATE": d / "state.json"}.items():
        monkeypatch.setattr(learn_cycle, name, path)
    monkeypatch.setattr(add_examples, "INBOX", d / "inbox.jsonl")
    monkeypatch.setattr(add_examples, "REJECTED", d / "rejected.jsonl")
    monkeypatch.setattr(add_examples, "USED", d / "used.json")
    monkeypatch.setattr(core, "CANDIDATES", tmp_path / "candidates")
    monkeypatch.setattr(core, "run_tests", lambda model_dir: (True, "stubbed in tests"))
    monkeypatch.setattr(core, "sms_false_alarms", lambda index, bands: 0.03)
    cfg = {**learn_cycle.DEFAULTS, "MIN_NEW_EXAMPLES": 5, "DEV_RECALL_TOLERANCE": 0.05,
           "FRESH_SYNTHETIC_WHEN_EMPTY": False}  # turned on only in the synthetic-dataset test
    monkeypatch.setattr(learn_cycle, "learning_config", lambda: dict(cfg))
    return {"tmp": tmp_path, "cfg": cfg}


def add_all():
    for label, text, kind in NEW:
        add_examples.add(text, label, kind)


def test_too_few_examples_does_nothing(learn):
    add_examples.add(NEW[0][1], "scam")
    assert learn_cycle.run()["status"] == "skipped"
    assert not learn_cycle.USED.exists()


def test_dry_run_measures_without_learning_or_using_examples(learn):
    add_all()
    r = learn_cycle.run(dry_run=True)
    assert r["status"] == "measured" and r["new_scams"] == 4 and r["new_honest"] == 2
    assert 0 <= r["caught_before"] <= 1 and not learn_cycle.USED.exists()


def test_learns_once_keeps_a_candidate_and_reports(learn):
    add_all()
    r = learn_cycle.run()
    assert r["status"] in ("accepted", "rejected", "nothing to add")
    assert len(json.loads(learn_cycle.USED.read_text())) == len(NEW)  # every example used once
    assert learn_cycle.run()["status"] == "skipped"                     # ... and never again
    latest = (learn_cycle.OUT / "latest.md").read_text()
    assert "Test before learning" in latest and "Not real-world accuracy" in latest
    if r["status"] == "accepted":
        best = json.loads(learn_cycle.BEST.read_text())
        assert best["name"] == r["new_version"] and (learn["tmp"] / "candidates" / best["name"]).is_dir()
        assert not r["promoted"]  # AUTO_PROMOTE is off by default


def test_gate_fails_closed_without_the_real_sms_file(learn, monkeypatch):
    monkeypatch.setattr(core, "sms_false_alarms", lambda index, bands: None)
    add_all()
    r = learn_cycle.run()
    if r["status"] == "nothing to add":
        pytest.skip("the engine already caught every example")
    assert r["status"] == "rejected" and any("sms.tsv" in c for c in r["failed_checks"])
    assert not learn_cycle.BEST.exists()
    kept = [json.loads(line) for line in learn_cycle.REJECTED.read_text().splitlines()]
    assert len(kept) == r["added_scams"] + r["added_honest"]  # nothing lost


def test_rejected_examples_can_be_retried_but_are_not_counted_as_new(learn, monkeypatch):
    monkeypatch.setattr(core, "sms_false_alarms", lambda index, bands: None)  # force a rejection
    add_all()
    first = learn_cycle.run()
    if first["status"] != "rejected":
        pytest.skip("the engine already caught every example")
    n = add_examples.retry_rejected()
    assert n == first["added_scams"] + first["added_honest"] and not learn_cycle.REJECTED.exists()
    monkeypatch.setattr(learn_cycle, "learning_config", lambda: {**learn["cfg"], "MIN_NEW_EXAMPLES": 1})
    monkeypatch.setattr(core, "sms_false_alarms", lambda index, bands: 0.03)
    again = learn_cycle.run()
    assert again["retried"] == n and again["new_scams"] == 0 and again["caught_before"] is None


def test_api_reports_are_learning_input(learn):
    learn_cycle.SCAM_REPORTS.write_text(json.dumps([{"id": "1", "text": NEW[0][1], "source": "website",
                                                     "created_at": "x", "embedding": []}]))
    items = learn_cycle.collect()
    assert items[0]["label"] == "scam" and items[0]["source"] == "report (website)"


def test_add_examples_rejects_bad_input(learn):
    with pytest.raises(ValueError):
        add_examples.add("text", "maybe")
    with pytest.raises(ValueError):
        add_examples.add("   ", "scam")


def test_feedback_endpoint_queues_an_example(learn, tmp_path):
    class NoEmbedder:
        is_loaded = False
    client = TestClient(create_app(Settings(reports_path=str(tmp_path / "r.json"), ai_text_model_dir=""),
                                   embedder=NoEmbedder()))
    r = client.post("/api/feedback", json={"text": "Pay the toll balance now at fastag-kyc.top", "label": "scam",
                                           "scam_type": "FASTag", "source": "extension"})
    assert r.status_code == 201 and r.json() == {"status": "queued"} and "fastag" not in r.text.lower()
    item = json.loads(add_examples.INBOX.read_text().splitlines()[0])
    assert item["label"] == "scam" and item["source"] == "api (extension)"
    assert client.post("/api/feedback", json={"text": "hi", "label": "maybe"}).status_code == 422
    honest = client.post("/api/feedback", json={"text": "See you at 6", "label": "not_scam"})
    assert honest.status_code == 201
    assert json.loads(add_examples.INBOX.read_text().splitlines()[1])["label"] == "legit"


def test_learning_schedule_is_every_2_hours_by_default():
    assert install_schedule.intervals()["learning"] == 2
    line = install_schedule.cron_line(2, "/usr/bin/python3", install_schedule.ROUTINES["learning"])
    assert line.startswith("0 */2 * * * ") and "learn_cycle.py" in line and "trustgraph-learning-routine" in line


def test_each_run_takes_the_next_fresh_chunk_of_your_dataset(learn, monkeypatch):
    learn["cfg"]["DATASET_CHUNK_ROWS"] = 3
    learn_cycle.DATASETS.mkdir(parents=True)
    with open(learn_cycle.DATASETS / "my_scams.csv", "w", encoding="utf-8") as f:
        f.write("text,label,scam_type\n" + "".join(f'"{t}",{"scam" if lab == "scam" else "honest"},{k or ""}\n'
                                                     for lab, t, k in NEW))
    state = learn_cycle.load_state()
    first = learn_cycle.next_dataset(learn["cfg"], state, core)
    assert first["name"] == "my_scams.csv rows 1-3 of 6" and len(first["rows"]) == 3
    first["commit"](state)
    second = learn_cycle.next_dataset(learn["cfg"], state, core)
    assert second["name"] == "my_scams.csv rows 4-6 of 6" and second["rows"][0]["text"] == NEW[3][1]
    second["commit"](state)
    assert learn_cycle.next_dataset(learn["cfg"], state, core) is None  # used up, synthetic off: nothing


def test_a_new_synthetic_dataset_when_yours_are_used_up(learn):
    learn["cfg"].update(FRESH_SYNTHETIC_WHEN_EMPTY=True, SYNTHETIC_SCAMS=8, SYNTHETIC_HONEST=8)
    r = learn_cycle.run()
    assert r["dataset"] == "synthetic_1000" and r["new_scams"] == 8 and r["new_honest"] == 8
    assert (learn_cycle.GENERATED / "synthetic_1000.jsonl").exists()
    assert learn_cycle.load_state()["synthetic_seeds"] == [1000]


def test_waits_the_interval_after_a_finished_run(learn):
    state = learn_cycle.load_state()
    state["last_finished"] = learn_cycle.time.strftime("%Y-%m-%dT%H:%M:%S")
    learn_cycle.save_state(state)
    assert learn_cycle.main([])["status"] == "skipped"            # just finished: wait 2 hours
    assert "waiting" not in str(learn_cycle.main(["--dry-run"]))  # a dry run never waits
