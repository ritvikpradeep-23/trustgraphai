import json
import re
import shutil
from pathlib import Path

import numpy as np
import pytest

from eval.generate import load_split
from eval.leakage import DATA, MANIFEST, filter_leaks, sha256, verify_manifest, write_manifest
from eval.metrics import calibrate, hits

FIELDS = {"id", "text", "label", "category", "split", "template_family", "channel", "language",
          "evasion_type", "difficulty", "novelty", "source"}


@pytest.fixture(scope="module")
def rows():
    return [r for split in ("corpus", "dev", "test") for r in load_split(DATA / f"{split}.jsonl")]


def test_leakage_filter_drops_near_copies_and_keeps_new_text():
    reference = ["Your parcel is held, pay the customs fee at the link today."]
    candidates = [{"id": "a", "text": "Your parcel is held, pay the customs fee at the link today!"},
                  {"id": "b", "text": "Dad, can you pick me up from football at six?"}]
    kept, removed = filter_leaks(candidates, reference)
    assert [r["id"] for r in kept] == ["b"]
    assert removed[0]["id"] == "a" and removed[0]["leak_similarity"] > 0.9


def test_every_row_has_every_field_and_valid_values(rows):
    for r in rows:
        assert FIELDS <= r.keys()
        assert r["label"] in ("scam", "legit")
        assert r["split"] in ("corpus", "dev", "test")
        assert r["channel"] in ("whatsapp", "sms", "email", "instagram", "messenger")
        assert r["novelty"] in (("seen", "unseen") if r["label"] == "scam" else ("n/a",))
    assert len({r["id"] for r in rows}) == len(rows)


def test_template_families_never_cross_splits(rows):
    split_of = {}
    for r in rows:
        assert split_of.setdefault(r["template_family"], r["split"]) == r["split"], r["template_family"]


def test_every_scam_category_is_in_the_test_set(rows):
    scam_cats = {r["category"] for r in rows if r["label"] == "scam"}
    test_cats = {r["category"] for r in rows if r["label"] == "scam" and r["split"] == "test"}
    assert scam_cats == test_cats and len(scam_cats) == 29


def _undo_evasion(text: str) -> str:
    """Reverse the generator's own tricks so links can be checked: spaced letters,
    ' dot ' and '[.]' obfuscation, hxxp, and leetspeak digits."""
    text = re.sub(r"(?<=\b\w) (?=\w)", "", text)  # "s e r v i c e29" -> "service29"
    text = text.replace("[.]", ".").replace(" dot ", ".").replace("hxxp", "http")
    return text.translate(str.maketrans("4301", "aeoi"))


def test_links_are_placeholders_or_reserved_domains(rows):
    url = re.compile(r"https?://\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|org|test|invalid|example)\b\S*")
    safe = re.compile(r"(example\.(com|org)|\.test|\.invalid|sh\.example)")
    for r in rows:
        for link in url.findall(_undo_evasion(r["text"])):
            assert safe.search(link), (r["id"], link)


def test_manifest_matches_the_frozen_test_file():
    manifest = verify_manifest()
    assert manifest["test_sha256"] == sha256(DATA / "test.jsonl")


def test_tampering_with_the_test_file_is_detected(tmp_path):
    test_copy = tmp_path / "test.jsonl"
    shutil.copy(DATA / "test.jsonl", test_copy)
    manifest_path = tmp_path / "MANIFEST.json"
    write_manifest(test_copy, 0, {}, 0, path=manifest_path)
    verify_manifest(manifest_path)
    with open(test_copy, "a", encoding="utf-8") as f:
        f.write(json.dumps({"id": "extra"}) + "\n")
    with pytest.raises(RuntimeError, match="Frozen test set changed"):
        verify_manifest(manifest_path)


def test_calibration_respects_ties_and_zero_scores():
    tied = np.r_[np.full(950, 0.04), np.linspace(0.1, 0.9, 50)]
    assert hits(tied, calibrate(tied)["caution"]).mean() <= 0.10
    mostly_zero = np.r_[np.zeros(970), np.linspace(0.2, 0.9, 30)]
    assert hits(mostly_zero, calibrate(mostly_zero)["caution"]).mean() <= 0.10
    spread = np.random.default_rng(0).random(1000)
    assert abs(hits(spread, calibrate(spread)["caution"]).mean() - 0.10) < 0.01
