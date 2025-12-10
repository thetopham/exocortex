from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Links(BaseModel):
    external_url: Optional[str] = None
    app: Optional[str] = None


class Content(BaseModel):
    text: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


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


class EventRead(EventCreate):
    id: str
    ingested_at: datetime


class EventRecord(BaseModel):
    """Internal representation used for persistence."""

    id: str
    timestamp: str
    source_system: str
    channel: str
    actor: Optional[str]
    direction: Optional[str]
    summary: Optional[str]
    content_text: Optional[str]
    content_data: Dict[str, Any]
    tags: List[str]
    links: Dict[str, Any]
    raw: Dict[str, Any]
    ingested_at: str

    @classmethod
    def from_event_create(cls, payload: EventCreate) -> "EventRecord":
        now = datetime.utcnow().isoformat()
        return cls(
            id=str(uuid4()),
            timestamp=payload.timestamp.isoformat(),
            source_system=payload.source_system,
            channel=payload.channel,
            actor=payload.actor,
            direction=payload.direction,
            summary=payload.summary,
            content_text=payload.content.text,
            content_data=payload.content.data,
            tags=[tag.lower() for tag in payload.tags],
            links=payload.links.dict(exclude_none=True),
            raw=payload.raw,
            ingested_at=now,
        )

    def as_response(self) -> EventRead:
        return EventRead(
            id=self.id,
            timestamp=datetime.fromisoformat(self.timestamp),
            source_system=self.source_system,
            channel=self.channel,
            actor=self.actor,
            direction=self.direction,
            summary=self.summary,
            content=Content(text=self.content_text, data=self.content_data),
            tags=self.tags,
            links=Links(**self.links),
            raw=self.raw,
            ingested_at=datetime.fromisoformat(self.ingested_at),
        )
