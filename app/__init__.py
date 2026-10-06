"""Compatibility namespace; canonical API source lives in backend/app."""
from pathlib import Path
__path__ = [str(Path(__file__).resolve().parents[1] / "backend" / "app")]
