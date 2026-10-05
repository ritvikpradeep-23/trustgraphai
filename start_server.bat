@echo off
rem Double-click to start the TrustGraph local service (scam check, AI-text check,
rem deepfake video check, accuracy results) at http://127.0.0.1:8000
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

echo Starting the TrustGraph local service. Keep this window open while you use it.
%PY% run_server.py
pause
