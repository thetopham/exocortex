from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class EventContent(BaseModel):
    text: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class EventLinks(BaseModel):
    external_url: Optional[str] = None
    app: Optional[str] = None


class EventCreate(BaseModel):
    timestamp: datetime
    source_system: str
    channel: str
    actor: Optional[str] = None
    direction: Optional[str] = None
    summary: Optional[str] = None
    content: EventContent = Field(default_factory=EventContent)
    tags: List[str] = Field(default_factory=list)
    links: EventLinks = Field(default_factory=EventLinks)
    raw: Dict[str, Any] = Field(default_factory=dict)


class Event(EventCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class EventResponse(BaseModel):
    id: str
    status: str = "ok"

