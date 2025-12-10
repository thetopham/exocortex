from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from . import db
from .models import Event, DEFAULT_LINKS

app = FastAPI(title="Sovereign Exocortex")
app.mount("/static", StaticFiles(directory="exocortex/static"), name="static")
templates = Jinja2Templates(directory="exocortex/templates")

db.init_db()


class EventContent(BaseModel):
    text: Optional[str] = None
    data: dict = Field(default_factory=dict)


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
    raw: dict = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: str
    timestamp: datetime
    source_system: str
    channel: str
    actor: Optional[str]
    direction: Optional[str]
    summary: Optional[str]
    content: EventContent
    tags: List[str]
    links: EventLinks
    raw: dict
    ingested_at: datetime

    @classmethod
    def from_event(cls, event: Event) -> "EventResponse":
        return cls(
            id=event.id,
            timestamp=event.timestamp,
            source_system=event.source_system,
            channel=event.channel,
            actor=event.actor,
            direction=event.direction,
            summary=event.summary,
            content=EventContent(text=event.content_text, data=event.content_data),
            tags=event.tags,
            links=EventLinks(**{**DEFAULT_LINKS, **event.links}),
            raw=event.raw,
            ingested_at=event.ingested_at,
        )


@app.get("/events", response_model=List[EventResponse])
def list_events(
    start_time: Annotated[Optional[datetime], Query(description="ISO8601 start time")]=None,
    end_time: Annotated[Optional[datetime], Query(description="ISO8601 end time")]=None,
    source_system: Annotated[Optional[str], Query()]=None,
    channel: Annotated[Optional[str], Query()]=None,
    tags: Annotated[Optional[str], Query(description="Comma-separated tags")]=None,
    limit: Annotated[int, Query(le=500, gt=0)] = 100,
):
    filters = []
    params = []
    if start_time:
        filters.append("timestamp >= ?")
        params.append(start_time.isoformat())
    if end_time:
        filters.append("timestamp <= ?")
        params.append(end_time.isoformat())
    if source_system:
        filters.append("source_system = ?")
        params.append(source_system)
    if channel:
        filters.append("channel = ?")
        params.append(channel)
    tag_terms: list[str] = []
    if tags:
        tag_terms = [t.strip().lower() for t in tags.split(",") if t.strip()]
        for tag in tag_terms:
            filters.append("tags LIKE ?")
            params.append(f"%{tag}%")

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"SELECT * FROM events {where_clause} ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    with db.get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [EventResponse.from_event(Event.from_row(row)) for row in rows]


@app.post("/events", response_model=EventResponse, status_code=201)
def create_event(event_in: EventCreate):
    event = Event(
        timestamp=event_in.timestamp,
        source_system=event_in.source_system,
        channel=event_in.channel,
        actor=event_in.actor,
        direction=event_in.direction,
        summary=event_in.summary,
        content_text=event_in.content.text,
        content_data=event_in.content.data,
        tags=event_in.tags,
        links=event_in.links.model_dump(),
        raw=event_in.raw,
    )

    with db.get_db() as conn:
        conn.execute(
            """
            INSERT INTO events (id, timestamp, source_system, channel, actor, direction, summary,
                                content_text, content_json, tags, links_json, raw_json, ingested_at)
            VALUES (:id, :timestamp, :source_system, :channel, :actor, :direction, :summary,
                    :content_text, :content_json, :tags, :links_json, :raw_json, :ingested_at)
            """,
            event.to_record(),
        )

    return EventResponse.from_event(event)


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    today = datetime.now(timezone.utc).astimezone()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    events = list_events(start_time=start, end_time=end, limit=200)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "events": events,
            "today": start.date().isoformat(),
        },
    )


@app.post("/add-note", response_class=HTMLResponse)
def add_note(
    request: Request,
    summary: Annotated[str, Form(...)],
    text: Annotated[Optional[str], Form("")]=None,
    tags: Annotated[Optional[str], Form("")]=None,
    source_system: Annotated[str, Form("manual_note")]="manual_note",
):
    if not summary.strip():
        raise HTTPException(status_code=400, detail="Summary is required")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    event_in = EventCreate(
        timestamp=datetime.now(timezone.utc),
        source_system=source_system,
        channel="note",
        actor="matt",
        direction="outbound",
        summary=summary.strip(),
        content=EventContent(text=text or summary.strip(), data={}),
        tags=tag_list,
        links=EventLinks(),
        raw={},
    )
    create_event(event_in)
    return read_root(request)
