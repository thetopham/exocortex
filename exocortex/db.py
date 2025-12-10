import json
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

DB_PATH = Path("data/events.db")


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    conn = get_connection(db_path)
    conn.execute(
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
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_system);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_channel ON events(channel);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_tags ON events(tags);")
    conn.commit()
    conn.close()


def serialize_tags(tags: Optional[Iterable[str]]) -> str:
    if tags is None:
        return json.dumps([])
    normalized = [t.strip().lower() for t in tags if t.strip()]
    return json.dumps(normalized)


def deserialize_tags(tags_text: str) -> list[str]:
    try:
        data = json.loads(tags_text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    return []
