import os
import numpy as np
import pytest

from training.data import balance, data_hash, group_folds, load
from training.phase0 import run


def test_cached_red_flags_follow_rule_changes(tmp_path, monkeypatch):
    # The cache key includes the rules, so a rule change never reuses old flag results.
    from training import scoring
    from trustgraph.similarity import detector as sim
    monkeypatch.setattr(scoring, "CACHE", tmp_path)
    monkeypatch.setattr(scoring.engine, "score_rows",
                        lambda rows, setting: [{"continuity": 0, "precedent": 0, "anomaly": 0} for _ in rows])
    rows = [{"id": "x", "text": "please keep this between us", "label": "scam"}]
    before = scoring.base_signals("t", rows)["flag_keep"][0]
    monkeypatch.setattr(sim, "RED_FLAGS", [])
    monkeypatch.setattr(sim, "_FLAGS", [])
    after = scoring.base_signals("t", rows)["flag_keep"][0]
    assert before < 1.0 and after == 1.0


def test_training_code_cannot_read_the_test_split():
    with pytest.raises(ValueError, match="never reads"):
        load("test")


def test_group_folds_keep_families_together_and_mix_labels():
    rows = load("corpus")
    for train, val in group_folds(rows, k=5, seed=0):
        assert not {rows[i]["template_family"] for i in train} & {rows[i]["template_family"] for i in val}
        assert {rows[i]["label"] for i in val} == {"scam", "legit"}
    assert sum(len(v) for _, v in group_folds(rows)) == len(rows)


def test_data_hash_ignores_order_and_catches_edits():
    rows = load("corpus")[:20]
    assert data_hash(rows) == data_hash(rows[::-1])
    edited = [dict(r) for r in rows]
    edited[0]["text"] += "!"
    assert data_hash(edited) != data_hash(rows)


def test_balance_flags_one_sided_groups():
    rows = [{"label": "scam", "x": "a"}] * 12 + [{"label": "legit", "x": "b"}] * 6 + [{"label": "scam", "x": "b"}] * 6
    flags = {t["value"]: t["flag"] for t in balance(rows, "x")}
    assert flags == {"a": True, "b": False}


def test_phase0_finds_no_missing_data(tmp_path):
    res = run(tmp_path)
    assert res["problems"] == []
    assert res["scam_categories"]["corpus"] == 29


def test_final_test_refuses_a_second_look(tmp_path):
    from training.final_test import main
    (tmp_path / "final_test_demo.json").write_text("{}")
    with pytest.raises(SystemExit, match="already scored"):
        main(["demo", "--out", str(tmp_path)])


def test_model_dir_variable_falls_back_to_models(tmp_path, monkeypatch):
    from trustgraph.paths import model_path
    monkeypatch.delenv("TRUSTGRAPH_MODEL_DIR", raising=False)
    assert model_path("risk_bands.json") == os.path.join("models", "risk_bands.json")
    (tmp_path / "risk_bands.json").write_text("{}")
    monkeypatch.setenv("TRUSTGRAPH_MODEL_DIR", str(tmp_path))
    assert model_path("risk_bands.json") == str(tmp_path / "risk_bands.json")
    assert model_path("anomaly_isolation_forest.joblib") == os.path.join("models", "anomaly_isolation_forest.joblib")


def test_hash_ignores_windows_line_endings(tmp_path):
    from eval.leakage import sha256
    unix, windows = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    unix.write_bytes(b'{"id": 1}\n{"id": 2}\n')
    windows.write_bytes(b'{"id": 1}\r\n{"id": 2}\r\n')
    assert sha256(unix) == sha256(windows)
    windows.write_bytes(b'{"id": 1}\r\n{"id": 3}\r\n')
    assert sha256(unix) != sha256(windows)
