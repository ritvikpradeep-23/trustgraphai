# ai/: everything AI in one place

All the models and the code that builds, tests and runs them. The website (`backend/`, `front end/`) and the browser
extension (`trustgraph_extension/`) are outside this folder. The website reaches in here only through
`backend/app/ai/`.

Run the commands from this folder (`cd ai`). The website itself is started from the repository root with
`python backend/run_server.py`.

## What's here

| Folder / file | What it is |
|---|---|
| `models/` | The live scam engine files, candidate versions, and (once trained, on your computer only) the AI-text model and the deepfake layer. See `models/README.md`. |
| `src/trustgraph/` | The 4-signal scam engine (similarity, anomaly, continuity, precedent) and its demo page. |
| `train_video.py`, `train_text.py`, `prepare_data.py`, `check_gpu.py` | Train the deepfake and AI-text detectors. |
| `video_detector.py`, `text_detector.py` | Score one video or text by hand. |
| `run_cycle.py`, `show_report.py` | The accuracy routine (every 2 hours) and its report. |
| `learn_cycle.py`, `add_examples.py` | The new-scam learning routine (one fresh dataset every 2 hours) and adding examples by hand. |
| `install_schedule.py` | Installs both routines in Windows Task Scheduler (or cron). |
| `detection_config.json` | Settings for both routines. |
| `run_website.py`, `start_website.bat` | The scam engine's own small test page. |
| `training/`, `routine/`, `eval/` | How the scam engine was improved and measured. |
| `scripts/` | Promote or roll back a version (`promote_model.py`), improvement rounds, EfficientNet training and demo. |
| `data/` | The engine's examples, development and test rounds, and (on your computer only) learning and video data. |
| `reports/`, `runs/` | Results of the rounds and the routines. |
| `backup/` | The demo-safe copy of the original engine. |
| `scratch/` | Old one-off check scripts. |
| `tests/` | The AI and routine tests: `python -m pytest tests -q` (no database needed). |
| `docs/` | How it works, step by step (`docs/HOW_IT_WORKS.md`), what it can't do and how to tune it (`docs/CAPABILITIES_AND_LIMITS.md`), and how the routines work. |
| `requirements-ai.txt` | The extra packages for the deepfake and AI-text detectors (PyTorch, transformers, OpenCV). |
| `move_local_files.py` | A one-time helper for after the move (below). |

## Just moved here? Do this once on your laptop

The files git tracks moved by themselves with `git pull`. Files that only exist on your computer stayed in their old
places: trained models, learning data, test batches, `eval/external/sms.tsv`, logs. Move them across, then re-point
the schedule:

```
python ai/move_local_files.py --dry-run     # shows what will move; nothing is changed
python ai/move_local_files.py               # moves them (never overwrites, deletes nothing)
python ai/install_schedule.py               # both 2-hour routines now run from ai/
```

Then update the Claude Desktop task `trustgraph-learning`: its working folder is now `...\trustgraphai\ai` (see
`docs/LEARNING_SUPERVISOR_TASK.md`).
