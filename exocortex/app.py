from __future__ import annotations

import json
from datetime import datetime, time
from typing import Dict, Optional

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from . import db
from .models import Event, EventContent, EventCreate, EventLinks, EventResponse

app = FastAPI(title="Sovereign Exocortex")
templates = Jinja2Templates(directory=str((db.DB_PATH.parent / "templates")))


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.post("/events", response_model=EventResponse)
def create_event(event: EventCreate) -> EventResponse:
    try:
        new_event = Event(**event.dict())
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db.save_event(new_event)
    return EventResponse(id=new_event.id)


@app.get("/events")
def list_events(
    start: Optional[datetime] = Query(default=None, description="ISO8601 start time"),
    end: Optional[datetime] = Query(default=None, description="ISO8601 end time"),
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = Query(default=None, description="Filter events containing tag"),
    limit: int = Query(default=100, le=500),
):
    events = db.fetch_events(
        start=start, end=end, source_system=source_system, channel=channel, tag=tag, limit=limit
    )
    return [dict(row) for row in events]


def _normalize_date(value: Optional[str], *, end_of_day: bool = False) -> Optional[datetime]:
    if not value:
        return None

    try:
        if "T" in value:
            return datetime.fromisoformat(value)
        parsed_date = datetime.fromisoformat(value)
        if parsed_date.time() == time.min and end_of_day:
            return parsed_date.replace(hour=23, minute=59, second=59)
        return parsed_date
    except ValueError:
        return None


@app.post("/notes", response_class=HTMLResponse)
def add_note(
    request: Request,
    content: str = Form(..., description="Note text"),
    tags: str = Form(default="", description="Comma separated tags"),
    summary: str = Form(default=""),
    source_system: str = Form(default="manual"),
    channel: str = Form(default="note"),
    actor: Optional[str] = Form(default=None),
    direction: Optional[str] = Form(default=None),
):
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    summary_text = summary.strip() or content.strip()[:80]

    event_create = EventCreate(
        timestamp=datetime.utcnow(),
        source_system=source_system or "manual",
        channel=channel or "note",
        actor=actor or None,
        direction=direction or None,
        summary=summary_text,
        content=EventContent(text=content.strip()),
        tags=tag_list,
        links=EventLinks(),
        raw={},
    )

    new_event = Event(**event_create.dict())
    db.save_event(new_event)

    return RedirectResponse(url="/", status_code=303)


@app.get("/", response_class=HTMLResponse)
def recent_events(
    request: Request,
    start: Optional[str] = Query(default=None, description="ISO date or datetime"),
    end: Optional[str] = Query(default=None, description="ISO date or datetime"),
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = Query(default=None, description="Filter events containing tag"),
):
    filters: Dict[str, Optional[str]] = {
        "start": start,
        "end": end,
        "source_system": source_system,
        "channel": channel,
        "tag": tag,
    }

    start_dt = _normalize_date(start)
    end_dt = _normalize_date(end, end_of_day=True)

    events = [dict(row) for row in db.fetch_events(start=start_dt, end=end_dt, source_system=source_system, channel=channel, tag=tag, limit=200)]

    for event in events:
        event["tags"] = json.loads(event.get("tags") or "[]")
        event["links"] = json.loads(event.get("links_json") or "{}")

    filter_options = {
        "source_systems": db.fetch_distinct_values("source_system"),
        "channels": db.fetch_distinct_values("channel"),
    }

    return templates.TemplateResponse(
        "events.html",
        {
            "request": request,
            "events": events,
            "filters": filters,
            "filter_options": filter_options,
        },
    )

