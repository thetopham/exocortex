from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Content(BaseModel):
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class Links(BaseModel):
    external_url: Optional[str] = Field(default=None, description="Link back to the original item")
    app: Optional[str] = Field(default=None, description="App-specific deep link, if available")


class EventBase(BaseModel):
    timestamp: datetime
    source_system: str
    channel: str
    actor: Optional[str] = None
    direction: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[Content] = None
    tags: Optional[List[str]] = None
    links: Optional[Links] = None
    raw: Optional[Dict[str, Any]] = None


class EventCreate(EventBase):
    """Payload for creating a new event."""


class EventResponse(EventBase):
    id: str
    ingested_at: datetime


__all__ = [
    "Content",
    "Links",
    "EventBase",
    "EventCreate",
    "EventResponse",
]
