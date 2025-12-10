import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .models import Event

DB_PATH = Path(os.getenv("EXO_DB_PATH", Path("data") / "exocortex.db"))


def _dict_factory(cursor: sqlite3.Cursor, row: Iterable) -> Dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = _dict_factory
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_system);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_channel ON events(channel);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_tags ON events(tags);")
    conn.commit()
    conn.close()


def insert_event(event: Event) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO events (
            id, timestamp, source_system, channel, actor, direction, summary,
            content_text, content_json, tags, links_json, raw_json, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps(event.content.data, ensure_ascii=False),
            json.dumps(event.tags, ensure_ascii=False),
            json.dumps(event.links.dict(), ensure_ascii=False),
            json.dumps(event.raw, ensure_ascii=False),
            event.ingested_at.isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return event.id


def query_events(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 100,
) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    query = ["SELECT * FROM events WHERE 1=1"]
    params: List = []

    if start:
        query.append("AND timestamp >= ?")
        params.append(start.isoformat())
    if end:
        query.append("AND timestamp <= ?")
        params.append(end.isoformat())
    if source_system:
        query.append("AND source_system = ?")
        params.append(source_system)
    if channel:
        query.append("AND channel = ?")
        params.append(channel)
    if tags:
        for tag in tags:
            query.append("AND tags LIKE ?")
            params.append(f"%{tag}%")

    query.append("ORDER BY timestamp DESC")
    query.append("LIMIT ?")
    params.append(limit)

    cursor.execute(" ".join(query), params)
    rows = cursor.fetchall()
    conn.close()
    return rows

