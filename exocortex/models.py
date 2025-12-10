import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class Event(EventCreate):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    ingested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True

