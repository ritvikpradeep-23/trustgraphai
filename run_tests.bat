@echo off
rem Double-click (or run from any folder) to run the project's tests.
rem It always runs inside the project folder, so pytest never searches your whole user folder.
cd /d "%~dp0"

set PY=python
%PY% --version >nul 2>&1 || set PY=py
%PY% --version >nul 2>&1 || (
  echo Python is not installed.
  echo Install Python 3.12 from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" on the first screen, then try again.
  pause
  exit /b 1
)

echo Running the tests in %CD% ...
%PY% -m pytest -q
pause
