from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db
from .models import EventCreate, EventRead, EventRecord

app = FastAPI(title="Sovereign Exocortex")

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))
STATIC_DIR = BASE_DIR / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup_event() -> None:
    db.init_db()


@app.post("/events", response_model=EventRead)
def create_event(event: EventCreate) -> EventRead:
    record = EventRecord.from_event_create(event)
    db.insert_event(
        {
            "id": record.id,
            "timestamp": record.timestamp,
            "source_system": record.source_system,
            "channel": record.channel,
            "actor": record.actor,
            "direction": record.direction,
            "summary": record.summary,
            "content_text": record.content_text,
            "content_data": record.content_data,
            "tags": record.tags,
            "links": record.links,
            "raw": record.raw,
            "ingested_at": record.ingested_at,
        }
    )
    return record.as_response()


@app.get("/events", response_model=List[EventRead])
def list_events(
    start_time: Optional[datetime] = Query(None, description="ISO timestamp"),
    end_time: Optional[datetime] = Query(None, description="ISO timestamp"),
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(100, le=500),
) -> List[EventRead]:
    rows = db.query_events(
        start_time=start_time.isoformat() if start_time else None,
        end_time=end_time.isoformat() if end_time else None,
        source_system=source_system,
        channel=channel,
        tag=tag,
        limit=limit,
    )

    records = [
        EventRecord(
            id=row["id"],
            timestamp=row["timestamp"],
            source_system=row["source_system"],
            channel=row["channel"],
            actor=row.get("actor"),
            direction=row.get("direction"),
            summary=row.get("summary"),
            content_text=row.get("content_text"),
            content_data=row.get("content_data", {}),
            tags=row.get("tags", []),
            links=row.get("links", {}),
            raw=row.get("raw", {}),
            ingested_at=row.get("ingested_at"),
        )
        for row in rows
    ]
    return [record.as_response() for record in records]


@app.get("/", response_class=HTMLResponse)
def timeline_page(
    request: Request,
    source_system: Optional[str] = None,
    tag: Optional[str] = None,
) -> HTMLResponse:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    events = db.query_events(
        start_time=today_start.isoformat(),
        source_system=source_system,
        tag=tag,
        limit=200,
    )
    return TEMPLATES.TemplateResponse(
        "timeline.html",
        {
            "request": request,
            "events": events,
            "filters": {"source_system": source_system or "", "tag": tag or ""},
        },
    )


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
