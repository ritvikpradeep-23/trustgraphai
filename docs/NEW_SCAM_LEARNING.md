# Learning new scams: the hourly learning routine

Scammers keep inventing new scripts. `learn_cycle.py` runs **every hour** and does two things:

- It **learns** from scams people report, and from honest messages that were wrongly flagged.
- It **measures**, before learning anything, how many of the new scams the engine already catches. That number is
  the live answer to "how likely is it to catch a scam it has never seen?".

It is a plain Python script. It never calls Claude, and everything stays on your computer.

## How new scams get in

| Way | Command / call |
|---|---|
| You type one | `python add_examples.py scam "the message" --type "fake electricity bill"` |
| An honest message that was wrongly flagged | `python add_examples.py honest "the message"` |
| A file of many | `python add_examples.py --csv new.csv` (columns `text,label[,scam_type]`, label `scam` or `honest`) |
| From the extension or website (once connected) | `POST /api/feedback` `{"text": ..., "label": "scam" or "not_scam", "scam_type": ...}` |
| Reported through the API | `POST /api/text/report`: picked up automatically from `data/scam_reports.json` |

**Honest examples matter as much as scams.** In the report-once experiment, learning from scam reports alone made the
engine *worse* (81% → 75% caught). Adding a few honest messages turned that into a gain (81% → 91%). All of that was
synthetic data.

## What one run does

1. **Collect:** gathers the examples it hasn't used before. With fewer than `MIN_NEW_EXAMPLES` (5) it stops
   straight away, so an hourly run with nothing new costs nothing. Each example is used once.
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
trend, and `GET /api/accuracy` includes it under `new_scam_learning`. Logs go to `logs/learn_cycle.log`.

## Settings (`detection_config.json`, `"learning"`)

| Setting | Default | Meaning |
|---|---|---|
| `LEARN_INTERVAL_HOURS` | 1 | How often it runs (whole hours, at least 1) |
| `MIN_NEW_EXAMPLES` | 5 | Fewer new examples than this: wait for more |
| `AUTO_PROMOTE` | false | Put accepted versions live by themselves |
| `DEV_RECALL_TOLERANCE` | 0 | 0 = dev recall may not drop at all (the improvement rounds' rule). 0.01 allows a drop of one point. |

**Install it:** `python install_schedule.py`. That installs both routines: accuracy every 2 hours and learning
every hour. `python install_schedule.py --show` checks them.

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
- **After the first reports**, rewordings of the same scam are caught far better: that's what the hourly learning is
  for. The first few victims of a brand-new scam are the hardest to protect.

Honest limits:

- Almost all test messages are synthetic, written by the same AI that built the detector, so these numbers flatter it.
- Reported examples are not verified by anyone. The gate limits the damage a wrong or malicious report can do, but
  can't make it zero.
- A handful of new scams per run is a tiny sample. Watch the trend in `show_report.py` over weeks, not one run.
- None of this is real-world accuracy.
