"""The known-fakes database: one table of fingerprints, looked up by Hamming
distance.

The connection string comes from FINGERPRINT_DB_URL (default
sqlite:///data/fingerprints.sqlite3). Only SQLite is implemented; another
database needs a class with the same methods (add, lookup, count, self_test).

Fast lookups as the table grows: each 64-bit hash is also stored as four
16-bit bands, each with an index. A record within 3 bits of the query must
share at least one band exactly, so the indexed query finds it without a
table scan. Re-compressed copies are usually that close. While the table has
at most FINGERPRINT_FULL_SCAN_MAX rows of a kind, the rest of the rows are
also compared directly, so every record within the threshold is found.
"""
import sqlite3
import threading
import uuid
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.fingerprint.hashing import bands, hamming, similarity, to_signed, to_unsigned

SCHEMA = """
CREATE TABLE IF NOT EXISTS fingerprints (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL CHECK (kind IN ('image', 'text')),
    label       TEXT NOT NULL,
    source      TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    hash        INTEGER NOT NULL,   -- pHash (image) or SimHash (text), signed 64-bit
    hash2       INTEGER,            -- dHash (image only)
    b0 INTEGER NOT NULL, b1 INTEGER NOT NULL, b2 INTEGER NOT NULL, b3 INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_fp_b0 ON fingerprints (kind, b0);
CREATE INDEX IF NOT EXISTS ix_fp_b1 ON fingerprints (kind, b1);
CREATE INDEX IF NOT EXISTS ix_fp_b2 ON fingerprints (kind, b2);
CREATE INDEX IF NOT EXISTS ix_fp_b3 ON fingerprints (kind, b3);
CREATE INDEX IF NOT EXISTS ix_fp_hash ON fingerprints (kind, hash);
"""

# One indexed lookup per band (a UNION, so SQLite uses ix_fp_b0..b3 rather
# than scanning every row of the kind).
BAND_QUERY = " UNION ".join(
    f"SELECT id, label, hash, hash2 FROM fingerprints WHERE kind = ? AND b{i} = ?" for i in range(4))


class StoreUnavailable(RuntimeError):
    pass


def sqlite_path(url: str) -> str:
    if url.startswith("sqlite:///"):
        return url[len("sqlite:///"):]
    raise StoreUnavailable(f"unsupported FINGERPRINT_DB_URL scheme (only sqlite:///path is implemented): {url.split(':', 1)[0]}")


class FingerprintStore:
    def __init__(self, url: str, full_scan_max: int = 20000):
        self.path = sqlite_path(url)
        self.full_scan_max = full_scan_max
        self._lock = threading.Lock()  # one writer at a time; SQLite handles readers
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as db:
                db.executescript(SCHEMA)
        except sqlite3.Error as exc:
            raise StoreUnavailable(str(exc)) from exc

    @contextmanager
    def _connect(self):
        try:
            conn = sqlite3.connect(self.path, timeout=5)
        except sqlite3.Error as exc:
            raise StoreUnavailable(str(exc)) from exc
        with closing(conn):
            with conn:  # commit on success, roll back on error
                yield conn

    def add(self, kind: str, hash_: int, label: str, source: str = "", hash2: int | None = None) -> str:
        record_id = uuid.uuid4().hex
        row = (record_id, kind, label, source, datetime.now(timezone.utc).isoformat(timespec="seconds"),
               to_signed(hash_), None if hash2 is None else to_signed(hash2), *bands(hash_))
        with self._lock, self._connect() as db:
            db.execute("INSERT INTO fingerprints (id, kind, label, source, created_at, hash, hash2, b0, b1, b2, b3) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
        return record_id

    def count(self, kind: str | None = None) -> int:
        with self._connect() as db:
            if kind:
                return db.execute("SELECT COUNT(*) FROM fingerprints WHERE kind = ?", (kind,)).fetchone()[0]
            return db.execute("SELECT COUNT(*) FROM fingerprints").fetchone()[0]

    def _candidates(self, db, kind: str, hash_: int):
        b = bands(hash_)
        rows = db.execute(BAND_QUERY, [v for band in b for v in (kind, band)]).fetchall()
        n = db.execute("SELECT COUNT(*) FROM fingerprints WHERE kind = ?", (kind,)).fetchone()[0]
        if n <= self.full_scan_max and n > len(rows):
            rows = db.execute("SELECT id, label, hash, hash2 FROM fingerprints WHERE kind = ?", (kind,)).fetchall()
        return rows

    def lookup(self, kind: str, hash_: int, threshold: int, hash2: int | None = None,
               threshold2: int | None = None, db=None) -> dict:
        """Closest record within the threshold(s):
        {db_match, similarity, matched_record_id, distance, label}."""
        def run(conn):
            best = None
            for record_id, label, h, h2 in self._candidates(conn, kind, hash_):
                d = hamming(hash_, to_unsigned(h))
                if d > threshold:
                    continue
                if hash2 is not None and h2 is not None and threshold2 is not None and hamming(hash2, to_unsigned(h2)) > threshold2:
                    continue
                if best is None or d < best[0]:
                    best = (d, record_id, label)
            if best is None:
                return {"db_match": False, "similarity": None, "matched_record_id": None}
            return {"db_match": True, "similarity": similarity(best[0]), "matched_record_id": best[1],
                    "distance": best[0], "label": best[2]}

        if db is not None:
            return run(db)
        with self._connect() as conn:
            return run(conn)

    def self_test(self) -> dict:
        """Write a probe fingerprint, find it again, then roll back, so the
        round trip is proven without leaving anything behind."""
        probe = 0x5A5A_F00D_C0DE_1234
        with self._lock:
            conn = sqlite3.connect(self.path, timeout=5)
            try:
                conn.execute("BEGIN")
                conn.execute("INSERT INTO fingerprints (id, kind, label, source, created_at, hash, hash2, b0, b1, b2, b3) "
                             "VALUES ('health-probe', 'text', 'probe', 'health', '', ?, NULL, ?, ?, ?, ?)",
                             (to_signed(probe), *bands(probe)))
                found = self.lookup("text", probe ^ 0b11, threshold=2, db=conn)
                records = conn.execute("SELECT COUNT(*) FROM fingerprints WHERE id != 'health-probe'").fetchone()[0]
            finally:
                conn.rollback()
                conn.close()
        return {"ok": found["matched_record_id"] == "health-probe", "records": records,
                "probe_found": found["matched_record_id"] == "health-probe"}
