from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import Event

DB_PATH = Path(__file__).resolve().parent / "exocortex.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
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


def save_event(event: Event) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO events (
                id, timestamp, source_system, channel, actor, direction, summary,
                content_text, content_json, tags, links_json, raw_json, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                event.id,
                event.timestamp.isoformat(),
                event.source_system,
                event.channel,
                event.actor,
                event.direction,
                event.summary,
                event.content.text,
                json.dumps(event.content.data),
                json.dumps(event.tags),
                json.dumps(event.links.dict()),
                json.dumps(event.raw),
                event.ingested_at.isoformat(),
            ),
        )


def _build_filters(
    start: Optional[datetime],
    end: Optional[datetime],
    source_system: Optional[str],
    channel: Optional[str],
    tag: Optional[str],
) -> Dict[str, Iterable]:
    clauses: List[str] = []
    params: List[str] = []

    if start is not None:
        clauses.append("timestamp >= ?")
        params.append(start.isoformat())
    if end is not None:
        clauses.append("timestamp <= ?")
        params.append(end.isoformat())
    if source_system:
        clauses.append("source_system = ?")
        params.append(source_system)
    if channel:
        clauses.append("channel = ?")
        params.append(channel)
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f"%{tag}%")

    where_clause = " WHERE " + " AND ".join(clauses) if clauses else ""
    return {"where": where_clause, "params": params}


def fetch_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 100,
) -> List[sqlite3.Row]:
    filters = _build_filters(start, end, source_system, channel, tag)
    query = (
        "SELECT * FROM events"
        f"{filters['where']}"
        " ORDER BY timestamp DESC"
        " LIMIT ?"
    )
    params: List[str] = list(filters["params"])
    params.append(str(limit))

    with get_connection() as conn:
        cur = conn.execute(query, params)
        return cur.fetchall()


def fetch_todays_events(limit: int = 100) -> List[sqlite3.Row]:
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    return fetch_events(start=start, end=end, limit=limit)


def fetch_distinct_values(column: str) -> List[str]:
    """Return distinct, non-empty values for a column in events."""

    if column not in {"source_system", "channel", "actor", "direction"}:
        raise ValueError("Unsupported column for distinct query")

    query = f"SELECT DISTINCT {column} FROM events WHERE {column} IS NOT NULL AND {column} != '' ORDER BY {column}"
    with get_connection() as conn:
        cur = conn.execute(query)
        return [row[0] for row in cur.fetchall() if row[0] is not None]

