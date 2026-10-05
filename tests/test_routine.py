import json
import shutil
import sys
from pathlib import Path

import pytest

from eval.leakage import max_similarity
from routine import core
from routine.generate import FINAL, IMPROVE, MANIFEST, OUT

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_round  # noqa: E402


def test_manifest_matches_and_detects_tampering(tmp_path):
    core.verify_manifest()
    copy = tmp_path / "rounds"
    shutil.copytree(OUT, copy)
    with open(copy / "round_05.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "extra"}) + "\n")
    with pytest.raises(RuntimeError, match="round_05.jsonl"):
        core.verify_manifest(copy / MANIFEST.name)


def test_final_rounds_are_locked():
    for n in FINAL:
        with pytest.raises(ValueError, match="frozen final test"):
            core.load_round(n)


def test_gate_needs_every_check():
    good = {"recall_caution": 0.6, "fpr_high": 0.01}
    scen_ok, scen_bad = {"n": 24, "failures": []}, {"n": 24, "failures": ["legit_new_phone (legit) -> Caution"]}
    assert core.gate(True, scen_ok, good, good, 0.05, 0.044)["passed"]
    assert not core.gate(False, scen_ok, good, good, 0.05, 0.044)["passed"]
    assert not core.gate(True, scen_bad, good, good, 0.05, 0.044)["passed"]
    assert not core.gate(True, scen_ok, {**good, "recall_caution": 0.5}, good, 0.05, 0.044)["passed"]
    assert not core.gate(True, scen_ok, {**good, "fpr_high": 0.05}, good, 0.05, 0.044)["passed"]
    assert not core.gate(True, scen_ok, good, good, 0.07, 0.044)["passed"]


def test_no_near_copies_across_rounds_and_families_stay_in_one_round():
    rounds = {n: [json.loads(line) for line in open(OUT / f"round_{n:02d}.jsonl", encoding="utf-8")]
              for n in range(1, 15)}
    family_round = {}
    for n, rows in rounds.items():
        for r in rows:
            assert family_round.setdefault(r["template_family"], n) == n
    earlier = [r["text"] for n in IMPROVE for r in rounds[n]] + [r["text"] for n in (1, 2) for r in rounds[n]]
    final = [r["text"] for n in FINAL for r in rounds[n]]
    sims, _ = max_similarity(final, earlier)
    assert max(sims) <= 0.9


def test_a_round_cannot_run_twice_or_out_of_order(tmp_path, monkeypatch):
    monkeypatch.setattr(core, "RUNS", tmp_path)
    (tmp_path / "history.csv").write_text("round,gate\n3,accepted\n4,accepted\n")
    with pytest.raises(SystemExit, match="already run"):
        run_round.run(4, commit=False)
    with pytest.raises(SystemExit, match="in order"):
        run_round.run(7, commit=False)
