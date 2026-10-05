@echo off
rem Double-click to start the TrustGraph test website.
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

echo Installing what the tester needs (the first time takes a minute or two)...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt || (
  echo Install failed. Check your internet connection and try again.
  pause
  exit /b 1
)

echo Starting the website. Keep this window open while you use it.
%PY% run_website.py
pause
