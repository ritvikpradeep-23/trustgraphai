"""Detectors + accuracy routine, end to end, without downloads.

EfficientNet is an UNTRAINED B0 of the real shape and the text model is a tiny
random RoBERTa, and the data is generated. So these tests check the plumbing
(splits, batches used once, lock, reports, schedule), never accuracy."""
import copy
import csv
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import torch

import detection_common
import install_schedule
import prepare_data
import run_cycle
import show_report
import text_detector
import train_text
import train_video
import video_detector
from app.deepfake_engine import efficientnet_wrapper as effnet
from detection_common import check_interval, group_split, make_batches

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import try_efficientnet_modes  # noqa: E402

REAL_CONFIG = detection_common.load_config()


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Point every path at tmp_path and use small batches."""
    cfg = copy.deepcopy(REAL_CONFIG)
    cfg["video"].update(test_batch_size=3, frames_per_video=4, model_path=str(tmp_path / "head.pt"))
    cfg["text"].update(test_batch_size=40, max_length=32, model_dir=str(tmp_path / "text_model"))
    for module in (prepare_data, run_cycle, train_video, train_text, video_detector, text_detector):
        monkeypatch.setattr(module, "load_config", lambda c=cfg: copy.deepcopy(c))
    monkeypatch.setattr(detection_common, "SPLITS_DIR", tmp_path / "splits")
    monkeypatch.setattr(prepare_data, "ROOT", tmp_path)
    monkeypatch.setattr(train_video, "CACHE", tmp_path / "cache")
    monkeypatch.setattr(run_cycle, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(run_cycle, "HISTORY", tmp_path / "reports" / "history.csv")
    monkeypatch.setattr(run_cycle, "LATEST", tmp_path / "reports" / "latest.md")
    monkeypatch.setattr(show_report, "HISTORY", tmp_path / "reports" / "history.csv")
    monkeypatch.setattr(show_report, "LATEST", tmp_path / "reports" / "latest.md")
    monkeypatch.setattr(show_report, "LEARNING_HISTORY", tmp_path / "reports" / "learning" / "history.csv")
    monkeypatch.setattr(effnet, "_loaded", {})
    try_efficientnet_modes.use_random_weights(effnet.MODEL_ID)  # no download
    return {"cfg": cfg, "tmp": tmp_path}


def tiny_text_model(folder: Path, texts: list[str]) -> Path:
    """A tokenizer trained on the test texts + a 1-layer RoBERTa, saved like a Hugging Face model."""
    from tokenizers import Tokenizer, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast, RobertaConfig, RobertaForSequenceClassification
    tok = Tokenizer(models.WordLevel(unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.train_from_iterator(texts, trainers.WordLevelTrainer(special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]"]))
    fast = PreTrainedTokenizerFast(tokenizer_object=tok, unk_token="[UNK]", pad_token="[PAD]",
                                   cls_token="[CLS]", sep_token="[SEP]")
    fast.save_pretrained(folder)
    config = RobertaConfig(vocab_size=fast.vocab_size, hidden_size=16, num_hidden_layers=1, num_attention_heads=2,
                           intermediate_size=32, max_position_embeddings=40, pad_token_id=fast.pad_token_id,
                           num_labels=2)
    torch.manual_seed(0)
    RobertaForSequenceClassification(config).save_pretrained(folder)
    return folder


def history_rows(env):
    path = env["tmp"] / "reports" / "history.csv"
    return list(csv.DictReader(open(path, newline="", encoding="utf-8"))) if path.exists() else []


# ---------------------------------------------------------------- config and splits
@pytest.mark.parametrize("bad", [0, 0.5, -2, 1.5, 24, "abc", None])
def test_interval_below_1_or_not_whole_hours_is_rejected(bad):
    with pytest.raises(ValueError):
        check_interval(bad)


def test_interval_accepts_whole_hours():
    assert check_interval(2) == 2 and check_interval("3") == 3 and check_interval(1.0) == 1


def test_groups_never_cross_sides_and_batches_are_fixed():
    rows = [{"text": f"t{i}", "label": i % 2, "group": f"g{i // 4}"} for i in range(400)]
    train, val, test = group_split(rows, {"train": 0.6, "val": 0.1, "test": 0.3}, seed=0)
    sides = [{r["group"] for r in part} for part in (train, val, test)]
    assert not (sides[0] & sides[1] or sides[0] & sides[2] or sides[1] & sides[2])
    assert len(train) + len(val) + len(test) == 400
    batches = make_batches(test, 50, seed=0)
    assert batches == make_batches(test, 50, seed=0)  # same input, same batches
    assert sum(map(len, batches)) == len(test) and min(map(len, batches)) >= 25


def test_splits_with_a_used_batch_are_never_replaced(env):
    prepare_data.main(["text", "--synthetic", "200"])
    with pytest.raises(SystemExit):
        prepare_data.main(["text", "--synthetic", "200"])  # exists: needs --force
    prepare_data.main(["text", "--synthetic", "200", "--force"])  # allowed: nothing used yet
    detection_common.mark_batch_used("text", "batch_001")
    with pytest.raises(SystemExit, match="Not replacing"):
        prepare_data.main(["text", "--synthetic", "200", "--force"])


# ---------------------------------------------------------------- text, end to end
def test_text_routine_uses_each_batch_once_then_stops(env, capsys):
    prepare_data.main(["text", "--synthetic", "300"])
    texts = [r["text"] for r in detection_common.read_csv(detection_common.split_dir("text") / "train.csv")]
    base = tiny_text_model(env["tmp"] / "tiny_base", texts)
    best = train_text.main(["--base-model", str(base), "--epochs", "1", "--batch-size", "16",
                            "--out", env["cfg"]["text"]["model_dir"]])
    assert 0 <= best["accuracy"] <= 1
    assert json.loads((Path(env["cfg"]["text"]["model_dir"]) / "training_info.json").read_text())["epoch"] == 1

    n_batches = len(detection_common.load_manifest("text")["batches"])
    seen = []
    for _ in range(n_batches):
        results = {r["kind"]: r for r in run_cycle.main()}
        assert results["text"]["status"] == "ok"
        seen.append(results["text"]["batch"])
    assert len(set(seen)) == n_batches  # every batch exactly once
    out = capsys.readouterr().out
    assert "Text: " in out and "accuracy, F1 " in out and "(n=" in out

    results = {r["kind"]: r for r in run_cycle.main()}  # batches exhausted
    assert results["text"]["status"] == "skipped" and "never reused" in results["text"]["reason"]
    assert "All" in (env["tmp"] / "logs" / "run_cycle.log").read_text() and len(history_rows(env)) == n_batches
    latest = (env["tmp"] / "reports" / "latest.md").read_text()
    assert "Text: skipped" in latest and "not real-world accuracy" in latest


def test_modified_batch_is_refused(env):
    prepare_data.main(["text", "--synthetic", "200"])
    texts = [r["text"] for r in detection_common.read_csv(detection_common.split_dir("text") / "train.csv")]
    tiny_text_model(Path(env["cfg"]["text"]["model_dir"]), texts)
    batch = detection_common.split_dir("text") / "test_batches" / "batch_001.csv"
    batch.write_text(batch.read_text() + "sneaky,1,x\n")
    result = run_cycle.run_detector("text", env["cfg"])
    assert result["status"] == "skipped" and "modified" in result["reason"]
    assert detection_common.used_batches("text") == []


def test_untrained_detector_is_skipped_without_using_a_batch(env):
    prepare_data.main(["text", "--synthetic", "200"])
    result = run_cycle.run_detector("text", env["cfg"])
    assert result["status"] == "skipped" and "not trained" in result["reason"]
    assert detection_common.used_batches("text") == []


# ---------------------------------------------------------------- video, end to end
def test_video_train_both_stages_then_routine(env):
    prepare_data.main(["video", "--synthetic", "30"])
    m = train_video.main(["--epochs", "2", "--unfreeze-last", "1", "--finetune-epochs", "1",
                          "--out", env["cfg"]["video"]["model_path"]])
    assert 0 <= m["accuracy"] <= 1
    saved = torch.load(env["cfg"]["video"]["model_path"], weights_only=True)
    assert "backbone_state_dict" in saved and saved["frames"] == 4
    result = video_detector.VideoDetector(env["cfg"]["video"]["model_path"]).score_video(
        detection_common.read_csv(detection_common.split_dir("video") / "val.csv")[0]["path"])
    assert 0 <= result["score"] <= 1 and result["frames"] >= 1
    results = {r["kind"]: r for r in run_cycle.main()}
    assert results["video"]["status"] == "ok" and results["text"]["status"] == "skipped"
    assert history_rows(env)[0]["detector"] == "video"


def test_frames_are_spread_over_the_whole_video(env):
    prepare_data.main(["video", "--synthetic", "30"])
    path = detection_common.read_csv(detection_common.split_dir("video") / "train.csv")[0]["path"]
    assert len(video_detector.sample_frames(path, 4)) == 4  # clips have 16 frames


# ---------------------------------------------------------------- lock, reports, schedule
def test_overlapping_run_is_skipped(env):
    (env["tmp"] / "logs").mkdir()
    (env["tmp"] / "logs" / "run_cycle.lock").write_text("pid 1")
    assert run_cycle.main() == []
    assert not (env["tmp"] / "reports" / "latest.md").exists()


def test_stale_lock_is_taken_over(env):
    import os
    import time
    (env["tmp"] / "logs").mkdir()
    lock = env["tmp"] / "logs" / "run_cycle.lock"
    lock.write_text("pid 1")
    old = time.time() - 7 * 3600
    os.utime(lock, (old, old))
    assert [r["kind"] for r in run_cycle.main()] == ["video", "text"]
    assert not lock.exists()


def test_show_report(env, capsys):
    show_report.main([])
    out = capsys.readouterr().out
    assert "No accuracy runs yet" in out and "No learning runs yet" in out
    run_cycle.main()
    show_report.main([])
    out = capsys.readouterr().out
    assert "Latest accuracy run" in out and "# Trend" in out


def test_schedule_definitions():
    line = install_schedule.cron_line(3, "/usr/bin/python3")
    assert line.startswith("0 */3 * * * ") and install_schedule.CRON_MARK in line and "run_cycle.py" in line
    from datetime import datetime
    xml = install_schedule.task_xml(3, r"C:\Python312\pythonw.exe", datetime(2026, 10, 5, 20, 0))
    root = ET.fromstring(xml.split("?>", 1)[1])  # parses: valid XML
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    assert root.find(".//t:Repetition/t:Interval", ns).text == "PT3H"
    assert root.find(".//t:StartWhenAvailable", ns).text == "false"  # a missed run is skipped
    assert root.find(".//t:MultipleInstancesPolicy", ns).text == "IgnoreNew"
    assert root.find(".//t:Exec/t:Command", ns).text.endswith("pythonw.exe")


def test_schedule_dry_run_changes_nothing(capsys):
    install_schedule.main(["--dry-run"])
    out = capsys.readouterr().out
    assert "every 2 hour(s)" in out and "run_cycle.py" in out


def test_show_and_remove_of_a_missing_windows_task_are_not_errors(monkeypatch, capsys):
    class Failed:
        returncode, stdout, stderr = 1, "", "ERROR: The system cannot find the file specified."
    monkeypatch.setattr(install_schedule.subprocess, "run", lambda *a, **k: Failed())
    install_schedule.windows("show", 2, False, install_schedule.ROUTINES["learning"])
    install_schedule.windows("remove", 2, False, install_schedule.ROUTINES["learning"])
    out = capsys.readouterr().out
    assert "TrustGraphLearningRoutine is not installed." in out and "nothing to remove" in out
    with pytest.raises(SystemExit):  # a failed install is still an error
        install_schedule.windows("install", 2, False, install_schedule.ROUTINES["learning"])
