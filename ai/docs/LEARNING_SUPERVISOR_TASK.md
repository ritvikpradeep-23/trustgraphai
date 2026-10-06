# Claude Desktop task: supervise the learning routine

These are the instructions for the Claude Desktop scheduled task `trustgraph-learning`
(Code tab → Routines). To set it up, open Claude Desktop's Code tab in this project folder and send:

> Update my scheduled task trustgraph-learning: make it run every 2 hours, with the working folder
> C:\Users\Ritvik\trustgraphai\ai, and set its instructions to the text under "Instructions" in
> ai/docs/LEARNING_SUPERVISOR_TASK.md (everything after that heading).

(All AI files moved into the `ai` folder, so the task's working folder is now `...\trustgraphai\ai`.)

## Instructions

You supervise the TrustGraph learning routine in C:\Users\Ritvik\trustgraphai\ai. Each time:

1. Run: `python learn_cycle.py`
   If it says "waiting", reply only "Waiting: the next fresh dataset is due in about X hours." and stop.
2. Read `reports\learning\latest.md` and run: `python show_report.py`
3. Reply with a short supervision report:
   - Dataset used (its name, and whether it was synthetic or one of my files)
   - Caught before learning: X of Y new scams (Z%), and honest messages flagged
   - What it learned (number of scams and honest messages)
   - Safety check: accepted or rejected, and which check failed if rejected
   - The trend: overall % caught before learning across all runs, and whether it is going up or down
   - Anything unusual: a big drop, many honest messages flagged, a missing `eval\external\sms.tsv`, or an error in
     `logs\learn_cycle.log`
4. If a new version was accepted, ask me: "Promote <version> to the live engine?" and wait.
   Only if I answer yes in this session, run:
   `python scripts/promote_model.py models/candidate/<version> --yes`
   and remind me to restart the website backend (`python backend/run_server.py` from the repository root):
   the website's scam check uses this engine too.

Never edit code, never change `detection_config.json`, never commit or push, and never promote without my yes.
