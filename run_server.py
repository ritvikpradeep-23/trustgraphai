"""Start the TrustGraph local service: python run_server.py

The built React frontend (front end/dist) and FastAPI API share one origin:
  /                     React workspace     /api/detect           pending AI check
  /api/workspace/*      sanitized history   /api/url/analyze      URL structure
  /health               service health      /docs                 API documentation

Configure DATABASE_URL in local .env and build the frontend first. The current
backend has no authentication or trained AI engine. Keep it private/local.
127.0.0.1 means only this computer can reach it.
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
