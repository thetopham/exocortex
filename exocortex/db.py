import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

DB_PATH = (Path(__file__).resolve().parent.parent / "data" / "exocortex.db").resolve()


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute(
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
        connection.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_system);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_events_channel ON events(channel);")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_events_tags ON events(tags);")


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def insert_event(
    *,
    id: str,
    timestamp: datetime,
    source_system: str,
    channel: str,
    actor: Optional[str],
    direction: Optional[str],
    summary: Optional[str],
    content_text: Optional[str],
    content_data: dict,
    tags: List[str],
    links: dict,
    raw: dict,
    ingested_at: datetime,
) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO events (
                id, timestamp, source_system, channel, actor, direction, summary,
                content_text, content_json, tags, links_json, raw_json, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                id,
                timestamp.isoformat(),
                source_system,
                channel,
                actor,
                direction,
                summary,
                content_text,
                json.dumps(content_data or {}),
                json.dumps(tags or []),
                json.dumps(links or {}),
                json.dumps(raw or {}),
                ingested_at.isoformat(),
            ),
        )
        connection.commit()


def fetch_events(
    *,
    from_timestamp: Optional[datetime] = None,
    to_timestamp: Optional[datetime] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
) -> Iterable[sqlite3.Row]:
    clauses = []
    params: List[object] = []

    if from_timestamp:
        clauses.append("timestamp >= ?")
        params.append(from_timestamp.isoformat())
    if to_timestamp:
        clauses.append("timestamp <= ?")
        params.append(to_timestamp.isoformat())
    if source_system:
        clauses.append("source_system = ?")
        params.append(source_system)
    if channel:
        clauses.append("channel = ?")
        params.append(channel)
    if tag:
        clauses.append("LOWER(tags) LIKE ?")
        params.append(f"%{tag.lower()}%")

    where_clause = ""
    if clauses:
        where_clause = " WHERE " + " AND ".join(clauses)

    query = (
        "SELECT * FROM events"
        f"{where_clause}"
        " ORDER BY timestamp DESC"
        " LIMIT ?"
    )
    params.append(limit)

    with get_connection() as connection:
        cursor = connection.execute(query, params)
        yield from cursor.fetchall()
