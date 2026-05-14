from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from . import db
from .models import Event, EventCreate, EventResponse

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


@app.get("/", response_class=HTMLResponse)
def recent_events(
    request: Request,
    start: Optional[str] = None,
    end: Optional[str] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = None,
):
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    filters = {
        "start": start,
        "end": end,
        "source_system": source_system,
        "channel": channel,
        "tag": tag,
    }

    events = [
        dict(row)
        for row in db.fetch_events(
            start=_parse_dt(start),
            end=_parse_dt(end),
            source_system=source_system,
            channel=channel,
            tag=tag,
            limit=200,
        )
    ]
    for event in events:
        event["tags"] = json.loads(event.get("tags") or "[]")
    return templates.TemplateResponse(
        "events.html", {"request": request, "events": events, "filters": filters}
    )

