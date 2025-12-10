import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(os.environ.get("EXO_DB_PATH", Path(__file__).resolve().parent.parent / "data" / "exocortex.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source_system TEXT NOT NULL,
                channel TEXT NOT NULL,
                actor TEXT,
                direction TEXT,
                summary TEXT,
                content_text TEXT,
                content_json TEXT,
                tags TEXT,
                links_json TEXT,
                raw_json TEXT,
                ingested_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_system);
            CREATE INDEX IF NOT EXISTS idx_events_channel ON events(channel);
            CREATE INDEX IF NOT EXISTS idx_events_tags ON events(tags);
            """
        )


@contextmanager
def get_db():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
