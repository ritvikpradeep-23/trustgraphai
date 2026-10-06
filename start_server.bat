@echo off
rem First follow COMBINED_SETUP.md. Starts the built frontend + pattern backend.
cd /d "%~dp0"

set PY=python
%PY% --version >nul 2>&1 || set PY=py
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
%PY% --version >nul 2>&1 || (
  echo Python is not installed.
  echo Install Python 3.12 from https://www.python.org/downloads/
  echo and tick "Add python.exe to PATH" on the first screen, then try again.
  pause
  exit /b 1
)

echo Starting the TrustGraph local service. Keep this window open while you use it.
%PY% run_server.py
pause
