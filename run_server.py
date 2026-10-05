"""Start the TrustGraph local service: python run_server.py

One server for everything, at http://127.0.0.1:8000 (the address the browser
extension uses by default):
  /                     test page            /api/score            scam check (extension)
  /api/text/ai-check    AI-written text?     /api/video/analyze    deepfake video
  /api/text/report, /api/text/analyze        similar scam reports
  /api/accuracy         latest accuracy-routine results
  /health               what is configured   /docs                 all endpoints, try them

It replaces run_website.py (which still works on its own). Don't run both: they
use the same port. 127.0.0.1 means only this computer can reach it.
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # models/ and data/ are loaded relative to the project folder
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    print(f"TrustGraph local service: http://127.0.0.1:{port}/  (API list: /docs, stop with Ctrl+C)")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)
