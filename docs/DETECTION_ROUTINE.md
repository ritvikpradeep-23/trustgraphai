# Deepfake video + AI-text detectors and the accuracy routine

Two detectors and a routine that measures them on fresh, labelled data every few hours:

- **Video:** your layer (the head in `app/deepfake_engine/combined_model.py`) on top of a frozen, pretrained
  `google/efficientnet-b0`.
- **Text:** a small pretrained language model (`distilroberta-base`) fine-tuned on human vs AI text.
- **Routine:** `run_cycle.py` takes the next unused labelled test batch, scores it and reports. It never trains
  or tunes anything. It is a plain Python script and never calls Claude.

All commands run from the project folder (`C:\Users\Ritvik\trustgraphai`).

## Quick start

```
python -m pip install -r requirements.txt
python check_gpu.py                                   # step 2: is the GPU usable?
python prepare_data.py text --hc3                     # step 3: text data (size printed before download)
python prepare_data.py video --folder D:\datasets\celebdf
python train_video.py                                 # step 4
python train_text.py                                  # step 5
python run_cycle.py                                   # step 6: one run by hand
python show_report.py                                 # step 7: latest run + trend
python install_schedule.py                            # step 8: every INTERVAL_HOURS
```

## What each file does

| File | What it does |
|---|---|
| `detection_config.json` | Settings: `INTERVAL_HOURS` (default 2), batch sizes, model paths, the split, `MAX_DOWNLOAD_GB` (1). |
| `detection_common.py` | Shared helpers: reads the config, makes splits, records which batches were used, computes the metrics. |
| `check_gpu.py` | Prints your GPU and checks PyTorch can calculate on it. |
| `prepare_data.py` | Turns a dataset into train / validation / numbered test batches, plus `manifest.json` with a SHA-256 hash per batch. |
| `video_detector.py` | Picks 16 frames spread over the video, crops the largest face, scores each face with EfficientNet + your head, and averages the scores. |
| `train_video.py` | Trains the head with EfficientNet frozen (stage 1). `--unfreeze-last N` adds stage 2. |
| `text_detector.py` | Loads the fine-tuned text model and gives each text a 0–1 "AI-written" score. |
| `train_text.py` | Fine-tunes `distilroberta-base` and keeps the epoch with the best validation F1. |
| `run_cycle.py` | The routine: one unused batch per detector, scored once, then marked as used. Writes the reports. |
| `show_report.py` | Prints `reports/latest.md` and the trend from `reports/history.csv`. |
| `install_schedule.py` | Installs, shows or removes the schedule (Task Scheduler on Windows, cron on macOS/Linux). |
| `.claude/settings.json` | Lets Claude Code run only these project scripts and `pip install -r requirements.txt`, and read and write only inside this folder. |
| `tests/test_detection_routine.py` | Offline tests of the plumbing: splits, batches used once, lock, reports, schedule. |

Where things are written (all on your laptop, never committed):

- `data/detection/`: splits, the list of used batches, and the face-crop cache.
- `models/efficientnet_head.pt`: the API uses the same file with `DEEPFAKE_MODE=efficientnet`.
- `models/text_detector/`
- `logs/`

`reports/history.csv` and `reports/latest.md` are yours to commit or not.

## Step 3: data plan

Only public datasets are used. A script never downloads anything over 1 GB on its own: it prints the name, source and
size first and stops, unless you re-run with `--allow-large`. The video datasets below are all far over 1 GB, so you
download them yourself.

### Video

| Dataset | How to get it | Access form? | Size |
|---|---|---|---|
| **Celeb-DF (v2)**: 590 real + 5,639 deepfake videos of celebrities | GitHub `yuezunli/celeb-deepfakeforensics` → fill in the request form → a download link is emailed | **Yes, you fill it in** | About 10 GB (check the page) |
| **FaceForensics++**: 1,000 real YouTube videos + versions made with several face-swap methods | GitHub `ondyari/FaceForensics` → fill in the Google form → you are emailed a download script | **Yes, you fill it in** | Depends on what you pick. Use the script's options for the smallest compression (`c40`) and only `original` + `Deepfakes`. It shows sizes before downloading. |
| **DFDC** (Facebook Deepfake Detection Challenge) | Kaggle competition `deepfake-detection-challenge` → sign in and accept the competition rules | No form, but you must accept the rules on Kaggle | Full set is about 470 GB in 50 parts. A small sample (`train_sample_videos`, 400 videos) is on the competition's data page. |

**Recommendation:** start with Celeb-DF v2. It's one moderate download, faces are frontal and large (the OpenCV face
detector handles them well), and its file names keep each person's videos together. Then run:

```
python prepare_data.py video --folder D:\datasets\celebdf
```

The folder needs a `real\` and a `fake\` sub-folder. For Celeb-DF, put `Celeb-real` + `YouTube-real` in `real\` and
`Celeb-synthesis` in `fake\`.

### Text

- **HC3** (`Hello-SimpleAI/HC3` on Hugging Face, licence CC-BY-SA-4.0): about 24,000 questions, each with human answers and
  ChatGPT answers.
  - `python prepare_data.py text --hc3` checks the file size, prints it, and stops if it's over 1 GB. HC3 is well
    under that.
  - It is public, so no account, token or API key is needed.
- **Any other dataset:** a CSV with columns `text,label` (1 = AI, 0 = human) and optionally `group`.
  Run `python prepare_data.py text --csv file.csv`.

### How the split works

- **Train 60%, validation 10%, test pool 30%**, split by **group**, never by row:
  - Text: one question with all its human and AI answers is one group.
  - Video: the first part of the file name is the group (the person in Celeb-DF and FaceForensics++).
  - So nothing in the test pool is a near-copy of something trained on.
- **The test pool is cut into numbered batches immediately**, before any training: `batch_001.csv`, `batch_002.csv`, …
  (50 videos or 200 texts each).
- **Training scripts only read `train.csv` and `val.csv`.** The batch files are hashed. If a batch changes after the
  split, the routine refuses to use it.
- **Splits are never replaced once any batch has been used**, because a new split could move tested items into training.

## How to train properly

**Video**
1. Train the head first: `python train_video.py`.
2. If validation is still poor with plenty of data, fine-tune the last blocks:
   `python train_video.py --unfreeze-last 2 --finetune-epochs 2`.
   - Stage 2 learns at 1/100 of the head's learning rate.
   - It saves the fine-tuned blocks next to the head (about 16 MB).
3. With Celeb-DF on a laptop GPU, stage 1 takes minutes. Most of the time goes to cutting faces out of the videos,
   and that is cached after the first run.

**Text**
- `python train_text.py` runs 2 epochs.
- The full HC3 training split takes a while on a laptop GPU. `--max-train 20000` is a reasonable first run.

**Rules for both**
- Change things (data, epochs, model) only by looking at **validation** numbers. The training scripts print them.
- Never look at test batches to decide anything. The routine only reads them after training is finished.
- Retrain whenever you like. The next routine run scores the next unused batch with the new model, and
  `history.csv` shows the new model fingerprint.

## The routine and the schedule

- `python install_schedule.py` installs the schedule:
  - **Windows:** a Task Scheduler task called `TrustGraphAccuracyRoutine`. It runs `run_cycle.py` every
    `INTERVAL_HOURS` with `pythonw.exe`, so no window pops up.
  - **macOS/Linux:** one marked crontab line.
- **Check it exists:** `python install_schedule.py --show`. On Windows you can also open Task Scheduler and look for
  the task.
- **Change the interval:**
  1. Edit `INTERVAL_HOURS` in `detection_config.json`. It must be a whole number from 1 to 23; anything below 1 is
     rejected.
  2. Run `python install_schedule.py` again. It replaces the old schedule.
- **Remove the schedule:** `python install_schedule.py --remove`.
- **Missed runs are skipped:**
  - If the laptop is off or asleep, that run is simply lost; nothing piles up.
  - A lock file (`logs/run_cycle.lock`) stops two runs overlapping.
  - A lock left behind by a crash is cleared after `LOCK_STALE_HOURS` (6).
- **When the batches run out:**
  - The routine logs a warning and skips that detector. Old batches are never reused.
  - To keep measuring, prepare a **new** held-out dataset in a fresh splits folder.
  - At the defaults, the HC3 test pool lasts roughly 10 days at one batch every 2 hours. A small video set lasts much
    less.
- **Untrained detectors:** a detector that isn't trained yet is skipped and keeps its batch.
- **Logs:** `logs/run_cycle.log`.

## What the percentages mean, and what they don't

- **They do mean:** how this model did on one batch of the prepared dataset that training never saw, scored once.
  The confusion matrix shows the kind of mistake:
  - real flagged as fake (false alarm)
  - fake that got through (miss)
- **The batches are small:**
  - 50 videos per batch: one video is 2 percentage points. Expect the number to wobble by several points between
    batches even with the same model.
  - Read the trend in `show_report.py`, not one run.
- **The model doesn't change between runs** unless you retrain. So identical-model runs only show how much the score
  varies from batch to batch. The routine becomes useful after you retrain: did the new model do better on batches it
  has never seen?
- **They are not real-world accuracy:**
  - Celeb-DF, FaceForensics++ and DFDC deepfakes come from specific older methods. Newer deepfakes, phone videos,
    heavy compression and side-on faces can score much worse.
  - HC3's AI text is 2022 ChatGPT answering questions. It's not SMS or WhatsApp messages, and not newer models.
  - A high number on these batches does not mean the detector is reliable on what your users will send.
- **The tiny end-to-end test numbers mean nothing.** Step 10 trains for one short epoch on a handful of examples, just
  to prove every piece runs. In the cloud check, the models were untrained and the data was generated, and the result
  was 50%: a coin toss, as expected.
