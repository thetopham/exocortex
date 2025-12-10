import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import db
from .models import Event, EventCreate, EventListResponse, EventResponse

app = FastAPI(title="Sovereign Exocortex", version="0.0.1")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.on_event("startup")
def startup_event() -> None:
    db.initialize_database()


def normalize_tags(tags: List[str]) -> List[str]:
    normalized = []
    for tag in tags:
        cleaned = tag.strip().lower()
        if cleaned:
            normalized.append(cleaned)
    return normalized


def row_to_event(row: Any) -> Event:
    content_data = json.loads(row["content_json"]) if row["content_json"] else {}
    tags = json.loads(row["tags"]) if row["tags"] else []
    links = json.loads(row["links_json"]) if row["links_json"] else {}
    raw = json.loads(row["raw_json"]) if row["raw_json"] else {}

    return Event(
        id=row["id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        source_system=row["source_system"],
        channel=row["channel"],
        actor=row["actor"],
        direction=row["direction"],
        summary=row["summary"],
        content={
            "text": row["content_text"],
            "data": content_data,
        },
        tags=tags,
        links=links,
        raw=raw,
        ingested_at=datetime.fromisoformat(row["ingested_at"]),
    )


def get_event_list(
    *,
    from_timestamp: Optional[datetime] = None,
    to_timestamp: Optional[datetime] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
) -> List[Event]:
    rows = db.fetch_events(
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        source_system=source_system,
        channel=channel,
        tag=tag,
        limit=limit,
    )
    return [row_to_event(row) for row in rows]


@app.post("/events", response_model=EventResponse)
def create_event(event: EventCreate) -> EventResponse:
    if not event.timestamp or not event.source_system or not event.channel:
        raise HTTPException(status_code=400, detail="timestamp, source_system, and channel are required")

    normalized_tags = normalize_tags(event.tags)
    content_text = event.content.text if event.content else None
    content_data = event.content.data if event.content else {}
    summary = event.summary or (content_text[:80] if content_text else None)

    event_id = str(uuid4())
    ingested_at = datetime.now(timezone.utc)

    db.insert_event(
        id=event_id,
        timestamp=event.timestamp,
        source_system=event.source_system,
        channel=event.channel,
        actor=event.actor,
        direction=event.direction,
        summary=summary,
        content_text=content_text,
        content_data=content_data,
        tags=normalized_tags,
        links=event.links.dict(),
        raw=event.raw,
        ingested_at=ingested_at,
    )

    return EventResponse(id=event_id)


@app.get("/events", response_model=EventListResponse)
def list_events(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = Query(default=None),
    source_system: Optional[str] = Query(default=None),
    channel: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> EventListResponse:
    events = get_event_list(
        from_timestamp=from_,
        to_timestamp=to,
        source_system=source_system,
        channel=channel,
        tag=tag,
        limit=limit,
    )
    return EventListResponse(events=events)


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    now = datetime.now(timezone.utc)
    start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    events = get_event_list(from_timestamp=start_of_day, limit=50)
    context: Dict[str, Any] = {
        "request": request,
        "events": events,
        "default_timestamp": now.isoformat(),
    }
    return templates.TemplateResponse("index.html", context)


@app.get("/health", response_model=dict)
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}
