"""Step 8: run run_cycle.py every INTERVAL_HOURS (detection_config.json, default 2).

    python install_schedule.py            # install (or update) the schedule
    python install_schedule.py --show     # check it exists
    python install_schedule.py --remove   # delete it
    python install_schedule.py --dry-run  # print what would be installed, change nothing

Windows: a Task Scheduler task named "TrustGraphAccuracyRoutine".
macOS / Linux: one line in your crontab, marked "# trustgraph-accuracy-routine".

Missed runs are skipped, never piled up: if the laptop is off or asleep at
run time, nothing catches up later (Task Scheduler "run as soon as possible
after a missed start" is OFF; cron never catches up). The lock file in
run_cycle.py also stops a run from starting while another is still going.
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

TASK_NAME = "TrustGraphAccuracyRoutine"
CRON_MARK = "# trustgraph-accuracy-routine"
SCRIPT = ROOT / "run_cycle.py"


def python_for_schedule() -> str:
    """On Windows use pythonw.exe (same install, no console window popping up)."""
    exe = Path(sys.executable)
    if platform.system() == "Windows":
        quiet = exe.with_name("pythonw.exe")
        if quiet.exists():
            return str(quiet)
    return str(exe)


# ---------------------------------------------------------------- Windows
def task_xml(hours: int, python: str, start: datetime) -> str:
    """Task Scheduler definition. The settings that matter:
    StartWhenAvailable=false  a missed run (laptop off) is skipped, not run late
    IgnoreNew                 never a second copy while one is running
    battery settings          also runs on battery (the default would skip it)
    ExecutionTimeLimit        a stuck run is stopped before the next one is due"""
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Description>TrustGraph accuracy routine: runs run_cycle.py every {hours} hour(s).</Description></RegistrationInfo>
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
      <Arguments>"{escape(str(SCRIPT))}"</Arguments>
      <WorkingDirectory>{escape(str(ROOT))}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""


def windows(action: str, hours: int, dry_run: bool):
    xml_file = None
    if action == "install":
        xml = task_xml(hours, python_for_schedule(), datetime.now().replace(second=0, microsecond=0)
                       + timedelta(minutes=5))
        if dry_run:
            print(xml)
            return
        with tempfile.NamedTemporaryFile("wb", suffix=".xml", delete=False) as f:
            f.write(xml.encode("utf-16"))  # Task Scheduler wants UTF-16 XML
            xml_file = f.name
        cmd = ["schtasks", "/Create", "/TN", TASK_NAME, "/XML", xml_file, "/F"]
    elif action == "remove":
        cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    else:
        cmd = ["schtasks", "/Query", "/TN", TASK_NAME, "/V", "/FO", "LIST"]
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
        windows("show", hours, False)


# ---------------------------------------------------------------- macOS / Linux
def cron_line(hours: int, python: str) -> str:
    """Every `hours` hours on the hour. With a value that doesn't divide 24 the
    gap across midnight is shorter (cron restarts counting each day)."""
    log = LOGS_DIR / "cron.log"
    return f"0 */{hours} * * * cd '{ROOT}' && '{python}' '{SCRIPT}' >> '{log}' 2>&1 {CRON_MARK}"


def read_crontab() -> list[str]:
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    except FileNotFoundError:  # cron not installed: nothing scheduled yet
        return []
    return result.stdout.splitlines() if result.returncode == 0 else []  # "no crontab" -> empty


def cron(action: str, hours: int, dry_run: bool):
    lines = [ln for ln in read_crontab() if CRON_MARK not in ln]  # drop our old line, keep everything else
    if action == "show":
        mine = [ln for ln in read_crontab() if CRON_MARK in ln]
        print("\n".join(mine) if mine else "No schedule installed.")
        return
    if action == "install":
        lines.append(cron_line(hours, python_for_schedule()))
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
        cron("show", hours, False)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--show", action="store_true")
    group.add_argument("--remove", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        hours = load_config()["INTERVAL_HOURS"]
    except ValueError as exc:  # below 1, or not whole hours: refuse to install
        raise SystemExit(f"detection_config.json: {exc}") from None
    action = "show" if args.show else "remove" if args.remove else "install"
    system = platform.system()
    print(f"{system}: {action}" + (f", every {hours} hour(s)" if action == "install" else ""))
    (windows if system == "Windows" else cron)(action, hours, args.dry_run)


if __name__ == "__main__":
    main()
