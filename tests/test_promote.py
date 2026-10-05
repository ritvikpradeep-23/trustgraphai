import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import promote_model  # noqa: E402

from training.bundle import write_bundle  # noqa: E402


def _bundle(tmp_path: Path) -> Path:
    src = tmp_path / "src.json"
    src.write_text('{"new": true}')
    return write_bundle("demo", {"thing.json": src}, {"thing.json": "models/thing.json"}, {"caution": 0.3, "high": 0.7},
                        data_hash="abc", n_train=1, seeds={"x": 0}, dev_metrics={"verdict": "adopt"},
                        card="test", root=tmp_path / "models" / "candidate")


def test_bundle_has_every_part(tmp_path):
    b = _bundle(tmp_path)
    assert {p.name for p in b.iterdir()} == {"thing.json", "risk_bands.json", "manifest.json", "MODEL_CARD.md"}
    m = json.loads((b / "manifest.json").read_text())
    assert m["synthetic_data"] and m["training_data_sha256"] == "abc" and "scikit-learn" in m["library_versions"]
    assert "synthetic" in (b / "MODEL_CARD.md").read_text()


def test_dry_run_changes_nothing_then_promote_and_rollback(tmp_path):
    b = _bundle(tmp_path)
    (tmp_path / "models" / "risk_bands.json").write_text('{"caution": 0.1, "high": 0.2}')
    assert promote_model.main([str(b), "--root", str(tmp_path)]) == 0
    assert not (tmp_path / "models" / "thing.json").exists()

    assert promote_model.main([str(b), "--root", str(tmp_path), "--yes"]) == 0
    assert json.loads((tmp_path / "models" / "risk_bands.json").read_text())["caution"] == 0.3
    assert (tmp_path / "models" / "thing.json").exists()

    assert promote_model.main(["--rollback", "--root", str(tmp_path)]) == 0
    assert json.loads((tmp_path / "models" / "risk_bands.json").read_text())["caution"] == 0.1
    assert not (tmp_path / "models" / "thing.json").exists()


def test_tampered_bundle_is_refused(tmp_path):
    b = _bundle(tmp_path)
    (b / "thing.json").write_text("changed")
    assert promote_model.main([str(b), "--root", str(tmp_path), "--yes"]) == 1
