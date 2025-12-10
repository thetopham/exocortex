import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DB_PATH = Path(os.getenv("EXO_DB_PATH", "exocortex.db"))


SCHEMA = """
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


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


@contextmanager
def get_connection() -> Iterable[sqlite3.Connection]:
    init_db()
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def insert_event(event: Dict[str, Any]) -> str:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO events (
                id, timestamp, source_system, channel, actor, direction,
                summary, content_text, content_json, tags, links_json,
                raw_json, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["timestamp"],
                event["source_system"],
                event["channel"],
                event.get("actor"),
                event.get("direction"),
                event.get("summary"),
                event.get("content_text"),
                json.dumps(event.get("content_data") or {}),
                json.dumps(event.get("tags") or []),
                json.dumps(event.get("links") or {}),
                json.dumps(event.get("raw") or {}),
                event["ingested_at"],
            ),
        )
        conn.commit()
    return event["id"]


def query_events(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    clauses = []
    params: List[Any] = []

    if start_time:
        clauses.append("timestamp >= ?")
        params.append(start_time)
    if end_time:
        clauses.append("timestamp <= ?")
        params.append(end_time)
    if source_system:
        clauses.append("source_system = ?")
        params.append(source_system)
    if channel:
        clauses.append("channel = ?")
        params.append(channel)
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f'%"{tag}"%')

    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = f"SELECT * FROM events{where_clause} ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    return [
        {
            **dict(row),
            "content_data": json.loads(row["content_json"] or "{}"),
            "tags": json.loads(row["tags"] or "[]"),
            "links": json.loads(row["links_json"] or "{}"),
            "raw": json.loads(row["raw_json"] or "{}"),
        }
        for row in rows
    ]


def latest_events(limit: int = 20) -> List[Dict[str, Any]]:
    return query_events(limit=limit)
