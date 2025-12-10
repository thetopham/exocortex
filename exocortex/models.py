import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class Content(BaseModel):
    text: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class Links(BaseModel):
    external_url: Optional[str] = None
    app: Optional[str] = None


class EventCreate(BaseModel):
    timestamp: datetime
    source_system: str
    channel: str
    actor: Optional[str] = None
    direction: Optional[str] = None
    summary: Optional[str] = None
    content: Content = Field(default_factory=Content)
    tags: List[str] = Field(default_factory=list)
    links: Links = Field(default_factory=Links)
    raw: Dict[str, Any] = Field(default_factory=dict)

    @validator("source_system", "channel")
    def non_empty(cls, value: str) -> str:  # noqa: D417
        if not value or not value.strip():
            raise ValueError("must not be empty")
        return value


class Event(EventCreate):
    id: str
    ingested_at: datetime

    @classmethod
    def from_row(cls, row: dict) -> "Event":
        def maybe_load(value: Any) -> Any:
            if value is None:
                return None
            if isinstance(value, (dict, list)):
                return value
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        return cls(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            source_system=row["source_system"],
            channel=row["channel"],
            actor=row["actor"],
            direction=row["direction"],
            summary=row["summary"],
            content=Content(
                text=row["content_text"],
                data=maybe_load(row["content_json"]) or {},
            ),
            tags=maybe_load(row["tags"]) or [],
            links=maybe_load(row["links_json"]) or {},
            raw=maybe_load(row["raw_json"]) or {},
            ingested_at=datetime.fromisoformat(row["ingested_at"]),
        )


class EventInsert:
    @staticmethod
    def build_id() -> str:
        return str(uuid4())
