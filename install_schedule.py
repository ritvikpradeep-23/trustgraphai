"""Step 8: install both routines on a schedule (settings in detection_config.json):

  accuracy  run_cycle.py   every INTERVAL_HOURS (default 2): scores one unused test batch
  learning  learn_cycle.py every learning.LEARN_INTERVAL_HOURS (default 2): one fresh dataset per run

    python install_schedule.py                  # install (or update) both
    python install_schedule.py --show           # check they exist
    python install_schedule.py --remove         # delete both
    python install_schedule.py --only learning  # just one of them (accuracy or learning)
    python install_schedule.py --dry-run        # print what would be installed, change nothing

Windows: Task Scheduler tasks "TrustGraphAccuracyRoutine" and "TrustGraphLearningRoutine".
macOS / Linux: one crontab line each, marked "# trustgraph-accuracy-routine" / "# trustgraph-learning-routine".

Missed runs are skipped, never piled up: if the laptop is off or asleep at
run time, nothing catches up later (Task Scheduler "run as soon as possible
after a missed start" is OFF; cron never catches up). Each script's lock
file also stops a run from starting while another of the same kind is still going.
"""
import argparse
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape

from detection_common import LOGS_DIR, ROOT, load_config

ROUTINES = {
    "accuracy": {"task": "TrustGraphAccuracyRoutine", "mark": "# trustgraph-accuracy-routine",
                 "script": ROOT / "run_cycle.py", "what": "accuracy routine (scores one unused test batch)"},
    "learning": {"task": "TrustGraphLearningRoutine", "mark": "# trustgraph-learning-routine",
                 "script": ROOT / "learn_cycle.py", "what": "new-scam learning routine"},
}
TASK_NAME, CRON_MARK, SCRIPT = (ROUTINES["accuracy"][k] for k in ("task", "mark", "script"))


def intervals() -> dict:
    """{routine: hours}. Both must be whole hours from 1 to 23 (anything below 1 is rejected)."""
    from detection_common import check_interval
    cfg = load_config()
    return {"accuracy": cfg["INTERVAL_HOURS"],
            "learning": check_interval(cfg.get("learning", {}).get("LEARN_INTERVAL_HOURS", 2))}


def python_for_schedule() -> str:
    """On Windows use pythonw.exe (same install, no console window popping up)."""
    exe = Path(sys.executable)
    if platform.system() == "Windows":
        quiet = exe.with_name("pythonw.exe")
        if quiet.exists():
            return str(quiet)
    return str(exe)


# ---------------------------------------------------------------- Windows
def task_xml(hours: int, python: str, start: datetime, routine: dict = ROUTINES["accuracy"]) -> str:
    """Task Scheduler definition. The settings that matter:
    StartWhenAvailable=false  a missed run (laptop off) is skipped, not run late
    IgnoreNew                 never a second copy while one is running
    battery settings          also runs on battery (the default would skip it)
    ExecutionTimeLimit        a stuck run is stopped before the next one is due"""
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>TrustGraph {routine['what']}: runs {routine['script'].name} every {hours} hour(s).</Description></RegistrationInfo>
  <Triggers>
    <TimeTrigger>
      <StartBoundary>{start.strftime('%Y-%m-%dT%H:%M:%S')}</StartBoundary>
      <Repetition><Interval>PT{hours}H</Interval><StopAtDurationEnd>false</StopAtDurationEnd></Repetition>
      <Enabled>true</Enabled>
    </TimeTrigger>
  </Triggers>
  <Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <StartWhenAvailable>false</StartWhenAvailable>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT{hours}H</ExecutionTimeLimit>
    <Enabled>true</Enabled>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{escape(python)}</Command>
      <Arguments>"{escape(str(routine['script']))}"</Arguments>
      <WorkingDirectory>{escape(str(ROOT))}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def windows(action: str, hours: int, dry_run: bool, routine: dict = ROUTINES["accuracy"]):
    xml_file, name = None, routine["task"]
    if action == "install":
        xml = task_xml(hours, python_for_schedule(), datetime.now().replace(second=0, microsecond=0)
                       + timedelta(minutes=5), routine)
        if dry_run:
            print(xml)
            return
        with tempfile.NamedTemporaryFile("wb", suffix=".xml", delete=False) as f:
            f.write(xml.encode("utf-16"))  # Task Scheduler wants UTF-16 XML
            xml_file = f.name
        cmd = ["schtasks", "/Create", "/TN", name, "/XML", xml_file, "/F"]
    elif action == "remove":
        cmd = ["schtasks", "/Delete", "/TN", name, "/F"]
    else:
        cmd = ["schtasks", "/Query", "/TN", name, "/V", "/FO", "LIST"]
    if dry_run:
        print(" ".join(cmd))
        return
    result = subprocess.run(cmd, capture_output=True, text=True)
    if xml_file:
        Path(xml_file).unlink(missing_ok=True)
    print((result.stdout or result.stderr).strip())
    if result.returncode != 0:
        raise SystemExit(f"schtasks failed ({result.returncode})")
    if action == "install":
        windows("show", hours, False, routine)


# ---------------------------------------------------------------- macOS / Linux
def cron_line(hours: int, python: str, routine: dict = ROUTINES["accuracy"]) -> str:
    """Every `hours` hours on the hour. With a value that doesn't divide 24 the
    gap across midnight is shorter (cron restarts counting each day)."""
    log = LOGS_DIR / f"cron_{routine['script'].stem}.log"
    return f"0 */{hours} * * * cd '{ROOT}' && '{python}' '{routine['script']}' >> '{log}' 2>&1 {routine['mark']}"


def read_crontab() -> list[str]:
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    except FileNotFoundError:  # cron not installed: nothing scheduled yet
        return []
    return result.stdout.splitlines() if result.returncode == 0 else []  # "no crontab" -> empty


def cron(action: str, hours: int, dry_run: bool, routine: dict = ROUTINES["accuracy"]):
    mark = routine["mark"]
    lines = [ln for ln in read_crontab() if mark not in ln]  # drop our old line, keep everything else
    if action == "show":
        mine = [ln for ln in read_crontab() if mark in ln]
        print("\n".join(mine) if mine else f"No schedule installed for {routine['script'].name}.")
        return
    if action == "install":
        lines.append(cron_line(hours, python_for_schedule(), routine))
    if dry_run:
        print("New crontab would be:\n" + "\n".join(lines))
        return
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["crontab", "-"], input="\n".join(lines) + "\n", text=True, check=True)
    except FileNotFoundError:
        raise SystemExit("The 'crontab' command was not found. Install cron (e.g. sudo apt install cron).") from None
    print("Removed." if action == "remove" else "Installed:")
    if action == "install":
        cron("show", hours, False, routine)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--show", action="store_true")
    group.add_argument("--remove", action="store_true")
    ap.add_argument("--only", choices=sorted(ROUTINES), help="just this routine (default: both)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        hours = intervals()
    except ValueError as exc:  # below 1, or not whole hours: refuse to install
        raise SystemExit(f"detection_config.json: {exc}") from None
    action = "show" if args.show else "remove" if args.remove else "install"
    system = platform.system()
    for name in ([args.only] if args.only else list(ROUTINES)):
        print(f"\n{system}: {action} the {ROUTINES[name]['what']}"
              + (f", every {hours[name]} hour(s)" if action == "install" else ""))
        (windows if system == "Windows" else cron)(action, hours[name], args.dry_run, ROUTINES[name])


if __name__ == "__main__":
    main()
