import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from .schemas import EventResponse

DB_PATH = Path("exocortex.db")


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
"""


def _ensure_indexes(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_source ON events(source_system);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_channel ON events(channel);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_tags ON events(tags);")


def normalize_tags(tags: Optional[Iterable[str]]) -> List[str]:
    if not tags:
        return []
    normalized = []
    for tag in tags:
        if tag is None:
            continue
        clean = tag.strip().lower()
        if clean and clean not in normalized:
            normalized.append(clean)
    return normalized


class EventStore:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(SCHEMA)
        _ensure_indexes(self.conn)
        self.conn.commit()

    def insert_event(self, payload: Dict[str, Any]) -> EventResponse:
        required_fields = ["timestamp", "source_system", "channel"]
        for field in required_fields:
            if payload.get(field) is None:
                raise ValueError(f"Missing required field: {field}")

        event_id = str(uuid4())
        timestamp: datetime = payload["timestamp"]
        content = payload.get("content") or {}
        content_text = content.get("text") if isinstance(content, dict) else None
        content_data = content.get("data") if isinstance(content, dict) else None

        links = payload.get("links") or {}
        tags = normalize_tags(payload.get("tags"))
        ingested_at = datetime.utcnow().isoformat()

        self.conn.execute(
            """
            INSERT INTO events (
                id, timestamp, source_system, channel, actor, direction, summary,
                content_text, content_json, tags, links_json, raw_json, ingested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                timestamp.isoformat(),
                payload.get("source_system"),
                payload.get("channel"),
                payload.get("actor"),
                payload.get("direction"),
                payload.get("summary"),
                content_text,
                json.dumps(content_data) if content_data is not None else None,
                json.dumps(tags) if tags else None,
                json.dumps(links) if links else None,
                json.dumps(payload.get("raw")) if payload.get("raw") is not None else None,
                ingested_at,
            ),
        )
        self.conn.commit()

        return EventResponse(
            id=event_id,
            timestamp=timestamp,
            source_system=payload.get("source_system"),
            channel=payload.get("channel"),
            actor=payload.get("actor"),
            direction=payload.get("direction"),
            summary=payload.get("summary"),
            content=payload.get("content"),
            tags=tags,
            links=payload.get("links"),
            raw=payload.get("raw"),
            ingested_at=datetime.fromisoformat(ingested_at),
        )

    def fetch_events(
        self,
        *,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        source_system: Optional[str] = None,
        channel: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 100,
    ) -> List[EventResponse]:
        query = "SELECT * FROM events WHERE 1=1"
        params: List[Any] = []

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        if source_system:
            query += " AND source_system = ?"
            params.append(source_system)
        if channel:
            query += " AND channel = ?"
            params.append(channel)
        if tag:
            query += " AND tags LIKE ?"
            params.append(f'%"{tag.strip().lower()}"%')

        query += " ORDER BY timestamp DESC"
        if limit:
            query += " LIMIT ?"
            params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_event(row) for row in rows]

    def _row_to_event(self, row: sqlite3.Row) -> EventResponse:
        tags = json.loads(row["tags"]) if row["tags"] else []
        content_data = json.loads(row["content_json"]) if row["content_json"] else None
        links = json.loads(row["links_json"]) if row["links_json"] else None
        raw = json.loads(row["raw_json"]) if row["raw_json"] else None

        content: Dict[str, Any] = {}
        if row["content_text"] is not None:
            content["text"] = row["content_text"]
        if content_data is not None:
            content["data"] = content_data

        return EventResponse(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source_system=row["source_system"],
            channel=row["channel"],
            actor=row["actor"],
            direction=row["direction"],
            summary=row["summary"],
            content=content or None,
            tags=tags,
            links=links,
            raw=raw,
            ingested_at=datetime.fromisoformat(row["ingested_at"]),
        )


__all__ = ["EventStore", "normalize_tags", "DB_PATH"]
