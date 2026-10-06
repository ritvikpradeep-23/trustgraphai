"""Start the combined app from either repository root or backend/."""
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]


def main():
    import uvicorn
    os.chdir(ROOT)
    port = int(os.getenv("PORT", "8000"))
    print(f"TrustGraph: http://127.0.0.1:{port}/app/analyze (Ctrl+C to stop)")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
