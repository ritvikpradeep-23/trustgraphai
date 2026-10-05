import numpy as np
import pytest

from training.data import balance, data_hash, group_folds, load
from training.phase0 import run


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
