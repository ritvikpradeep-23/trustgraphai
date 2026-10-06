"""Read-only connection/schema check; never print connection strings."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text
from app.core.database import engine

if __name__ == "__main__":
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            missing = [table for table in ("submissions", "detections", "reports", "report_matches", "relationships") if not inspect(connection).has_table(table)]
        print("Database connection: OK (read-only check)")
        print("Schema: " + ("ready" if not missing else "missing " + ", ".join(missing)))
        sys.exit(1 if missing else 0)
    except Exception as error:
        print("Database check failed: " + type(error).__name__ + ". Check DATABASE_URL, network access, and credentials locally.")
        sys.exit(1)
