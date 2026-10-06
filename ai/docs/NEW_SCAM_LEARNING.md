# Learning new scams: the learning routine (a fresh dataset every 2 hours)

Scammers keep inventing new scripts. `learn_cycle.py` takes **one fresh dataset it has never used**, trains on it,
and then **waits 2 hours after finishing** before taking the next one. Each run:

- It **measures**, before learning anything, how many of the dataset's scams the engine already catches. That's the
  running answer to "how likely is it to catch a scam it hasn't seen?".
- It **learns** the scams it missed and the honest messages it wrongly flagged, then keeps the new version only if
  it passes the safety gate.

It is a plain Python script. It never calls Claude, and everything stays on your computer.

## Where each run's fresh dataset comes from

1. **Your datasets first:**
   - Drop files into `data/learning/datasets/`: CSV with columns `text,label[,scam_type]` (label `scam` or `honest`),
     or JSONL with the same fields.
   - They're used in file-name order.
   - A big file is used `DATASET_CHUNK_ROWS` (300) rows per run, so one file gives several fresh datasets.
   - A file you edit afterwards starts again from the top, but rows already learned are skipped.
2. **When your datasets are used up, a new synthetic dataset:**
   - 60 scams and 120 honest messages, made with a never-used seed (`routine/fresh.py`).
   - It uses only the improvement-round templates. It never copies the development rounds (which the gate relies
     on) or the final-test rounds.
   - Near-copies of anything used before are dropped.
   - It's saved in `data/learning/generated/`. `FRESH_SYNTHETIC_WHEN_EMPTY: false` turns this off.
   - **Honest limit:** these reuse scam *types* the engine has already studied. They test new wordings and evasion
     tricks, not new kinds of scam. Real new scams come from your datasets and reports.
3. **Plus anything reported since the last run**, from the list below.

## How single new scams get in

| Way | Command / call |
|---|---|
| You type one | `python add_examples.py scam "the message" --type "fake electricity bill"` |
| An honest message that was wrongly flagged | `python add_examples.py honest "the message"` |
| A file of many | `python add_examples.py --csv new.csv` (columns `text,label[,scam_type]`, label `scam` or `honest`) |
| An older reports file | `data/scam_reports.json`, if present, is picked up automatically |

Reports made on the website are stored in PostgreSQL (the website keeps all its data there) and are **not** read by
the routine yet. Export them to a CSV and use `add_examples.py --csv` until that is connected.

**Honest examples matter as much as scams.** In the report-once experiment, learning from scam reports alone made the
engine *worse* (81% → 75% caught). Adding a few honest messages turned that into a gain (81% → 91%). All of that was
synthetic data.

## What one run does

1. **Collect:** takes the next fresh dataset plus new reports. Each example is used once, ever.
   - It runs only if `LEARN_INTERVAL_HOURS` (2) have passed since the last run *finished*. A scheduled start that
     comes too early just logs "waiting". `--now` skips the wait.
2. **Test before learning:** scores the new examples with the current best version. "Caught X of Y new scams" is
   recorded **before** the engine learns them.
3. **Learn:**
   - The scams it missed join its scam examples.
   - The honest messages it flagged join its honest examples.
   - It is then rebuilt and its cut-offs re-set on the development rounds.
4. **Safety check (gate):** a new version is kept only if:
   - all tests pass
   - all 24 demo scenarios keep their result
   - dev recall is not lower, and dev High false alarms are not higher
   - real UK SMS false alarms are at most 2 points above the starting engine
   - the real SMS file (`eval/external/sms.tsv`) is present. Without it, nothing is accepted.
5. **Result:**
   - **Accepted:** it becomes the best version, `models/candidate/learn_<time>/`. The next run builds on it.
   - **Rejected:** the examples it would have learned are saved in `data/learning/rejected.jsonl`, so nothing is lost.
     Check them, delete any you don't trust, then run `python add_examples.py --retry-rejected`. Retried examples
     don't count toward the "caught before learning" figure, because they have been tested once already.
6. **The live engine doesn't change until you promote it:**
   - Run `python scripts/promote_model.py models/candidate/<version> --yes`, then restart the server.
     `--rollback` undoes it.
   - Setting `"AUTO_PROMOTE": true` in `detection_config.json` makes accepted versions go live automatically, with a
     backup first. The server still needs a restart to load them.

Reports go to `reports/learning/latest.md` and `reports/learning/history.csv`. `python show_report.py` shows the
trend. Logs go to `logs/learn_cycle.log`.

## Settings (`detection_config.json`, `"learning"`)

| Setting | Default | Meaning |
|---|---|---|
| `LEARN_INTERVAL_HOURS` | 2 | Hours to wait after a run finishes before the next dataset (whole hours, at least 1) |
| `DATASET_CHUNK_ROWS` | 300 | Rows of your dataset files used per run |
| `FRESH_SYNTHETIC_WHEN_EMPTY` | true | Make a new synthetic dataset when yours are used up |
| `SYNTHETIC_SCAMS` / `SYNTHETIC_HONEST` | 60 / 120 | Size of each synthetic dataset |
| `MIN_NEW_EXAMPLES` | 5 | Fewer new examples than this: wait for more |
| `AUTO_PROMOTE` | false | Put accepted versions live by themselves |
| `DEV_RECALL_TOLERANCE` | 0 | 0 = dev recall may not drop at all (the improvement rounds' rule). 0.01 allows a drop of one point. |

**Supervise it from Claude Code:** `docs/LEARNING_SUPERVISOR_TASK.md` has the instructions for a Claude Desktop
scheduled task that runs the routine every 2 hours and reports each dataset's result (and asks before promoting).

**Or install it without Claude:** `python install_schedule.py`. That installs both routines, each every 2 hours. `python install_schedule.py --show` checks them.

**First, copy the real SMS file** from your ai-model folder, or no version can pass the gate:

```
mkdir eval\external
copy ..\ai-model\eval\external\sms.tsv eval\external\
```

## How likely is it to catch a totally new scam?

Short answer: **about 6 in 10 for a brand-new scam type, on synthetic data. In real life it's unknown, and probably
lower.** It reaches about 9 in 10 once a few examples of that scam have been reported and learned.

The evidence, all **synthetic data** except where marked:

| Measurement | Caught |
|---|---|
| Leave-one-type-out: a scam type removed from the examples, then tested on it (mean of 29 types, best example set) | **75%** (57% with the original examples) |
| Locked final test, rounds 13-14 (120 scams, 25 types, many new): best version vs starting engine | **65%** vs 52%, with 0% honest messages flagged |
| Learning routine on two fresh synthetic datasets (scam types it had studied, new wordings), before learning | 88% and 83% (53/60, 50/60) |
| Learning routine, this session: 14 brand-new scams (LPG e-KYC, 5G SIM, tax refund, OLX army buyer, subscription renewal…), before learning | **64%** (9 of 14) |
| After learning 3 reported tax-refund scams: 3 reworded tax-refund scams it hadn't seen | 1 of 3 before → **3 of 3** after, honest tax messages still 0 of 2 flagged |
| Report-once experiment: fresh batch after reports + honest examples were learned | 81% → **91%** |

What decides whether a new scam gets caught:

- **Caught well:** scams that *ask* for something risky, such as an OTP, card details, a fee, a link to "verify",
  remote access, or gift cards. The red-flag rules and similar wording catch these even in a new costume.
- **Missed:**
  - scams with **no ask yet**, like a friendly "wrong number" or "are you free?". Wording can't catch these;
    sender history has to.
  - very new formats, like a fake e-challan or KYC renewal worded calmly. These were caught 0 of 4 and 3 of 6 on the
    final test.
- **After the first reports**, rewordings of the same scam are caught far better: that's what the learning routine is
  for. The first few victims of a brand-new scam are the hardest to protect.

Honest limits:

- Almost all test messages are synthetic, written by the same AI that built the detector, so these numbers flatter it.
- Reported examples are not verified by anyone. The gate limits the damage a wrong or malicious report can do, but
  can't make it zero.
- A handful of new scams per run is a tiny sample. Watch the trend in `show_report.py` over weeks, not one run.
- None of this is real-world accuracy.
