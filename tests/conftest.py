"""Run every test from the project folder, whichever folder pytest was started in.

The engine loads models/ and data/ relative to the project root (run_website.py
does the same os.chdir), so without this, `python -m pytest <project path>`
started from another folder fails with FileNotFoundError.
"""
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parents[1])
