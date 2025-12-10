from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Content(BaseModel):
    text: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class Links(BaseModel):
    external_url: Optional[str] = None
    app: Optional[str] = None


class EventBase(BaseModel):
    timestamp: datetime
    source_system: str
    channel: str
    actor: Optional[str] = None
    direction: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[Content] = None
    tags: List[str] = Field(default_factory=list)
    links: Links = Field(default_factory=Links)
    raw: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("tags", mode="before")
    @classmethod
    def ensure_tags_list(cls, value: Optional[Any]) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(tag) for tag in value]
        if isinstance(value, str):
            return [value]
        return list(value)


class EventCreate(EventBase):
    pass


class Event(EventBase):
    id: str
    ingested_at: datetime


class EventResponse(BaseModel):
    id: str
    status: str = "ok"


class EventListResponse(BaseModel):
    events: List[Event]
