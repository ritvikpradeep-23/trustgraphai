"""Start the TrustGraph test website: python run_website.py"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # models/ and data/ are loaded relative to the repository root
sys.path.insert(0, str(ROOT / "src"))

from trustgraph.web.server import main  # noqa: E402

main(open_browser="--no-browser" not in sys.argv)
