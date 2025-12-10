from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_LINKS = {"external_url": None, "app": None}


def _normalize_tags(tags: Iterable[str] | None) -> List[str]:
    if not tags:
        return []
    return sorted({tag.strip().lower() for tag in tags if tag.strip()})


def parse_tags(tag_string: str | None) -> List[str]:
    if not tag_string:
        return []
    try:
        parsed = json.loads(tag_string)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return [part for part in tag_string.split(",") if part]


@dataclass
class Event:
    timestamp: datetime
    source_system: str
    channel: str
    actor: Optional[str] = None
    direction: Optional[str] = None
    summary: Optional[str] = None
    content_text: Optional[str] = None
    content_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    links: Dict[str, Any] = field(default_factory=lambda: DEFAULT_LINKS.copy())
    raw: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ingested_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row) -> "Event":
        return cls(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source_system=row["source_system"],
            channel=row["channel"],
            actor=row["actor"],
            direction=row["direction"],
            summary=row["summary"],
            content_text=row["content_text"],
            content_data=json.loads(row["content_json"]) if row["content_json"] else {},
            tags=parse_tags(row["tags"]),
            links=json.loads(row["links_json"]) if row["links_json"] else DEFAULT_LINKS.copy(),
            raw=json.loads(row["raw_json"]) if row["raw_json"] else {},
            ingested_at=datetime.fromisoformat(row["ingested_at"]),
        )

    def to_record(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "source_system": self.source_system,
            "channel": self.channel,
            "actor": self.actor,
            "direction": self.direction,
            "summary": self.summary,
            "content_text": self.content_text,
            "content_json": json.dumps(self.content_data) if self.content_data else None,
            "tags": json.dumps(_normalize_tags(self.tags)),
            "links_json": json.dumps(self.links) if self.links else None,
            "raw_json": json.dumps(self.raw) if self.raw else None,
            "ingested_at": self.ingested_at.isoformat(),
        }
