import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request

from . import db
from .models import Event, EventCreate

app = FastAPI(title="Sovereign Exocortex")
templates = Jinja2Templates(directory="exocortex/templates")


def ensure_db_initialized():
    db.init_db()


@app.on_event("startup")
async def startup_event():
    ensure_db_initialized()


@app.post("/events", response_model=Event)
async def create_event(payload: EventCreate) -> Event:
    ensure_db_initialized()
    event = Event(**payload.dict())
    try:
        db.insert_event(event)
    except Exception as exc:  # pragma: no cover - surface DB errors cleanly
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return event


@app.get("/events", response_model=List[Event])
async def list_events(
    start: Optional[datetime] = Query(None, description="Filter events after this timestamp"),
    end: Optional[datetime] = Query(None, description="Filter events before this timestamp"),
    source_system: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    limit: int = Query(100, ge=1, le=500),
) -> List[Event]:
    ensure_db_initialized()
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else None
    rows = db.query_events(
        start=start,
        end=end,
        source_system=source_system,
        channel=channel,
        tags=tag_list,
        limit=limit,
    )
    events: List[Event] = []
    for row in rows:
        events.append(
            Event(
                id=row["id"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                source_system=row["source_system"],
                channel=row["channel"],
                actor=row.get("actor"),
                direction=row.get("direction"),
                summary=row.get("summary"),
                content={
                    "text": row.get("content_text"),
                    "data": json.loads(row.get("content_json")) if row.get("content_json") else {},
                },
                tags=json.loads(row.get("tags")) if row.get("tags") else [],
                links=json.loads(row.get("links_json")) if row.get("links_json") else {},
                raw=json.loads(row.get("raw_json")) if row.get("raw_json") else {},
                ingested_at=datetime.fromisoformat(row["ingested_at"]),
            )
        )
    return events


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    ensure_db_initialized()
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    events = await list_events(start=start, end=end, limit=200)  # type: ignore[arg-type]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "events": events,
        },
    )


@app.post("/add", response_class=HTMLResponse)
async def add_manual_note(
    request: Request,
    summary: str = Form(...),
    content: str = Form(""),
    tags: str = Form(""),
) -> HTMLResponse:
    payload = EventCreate(
        timestamp=datetime.utcnow(),
        source_system="manual",
        channel="note",
        actor="self",
        direction="outbound",
        summary=summary,
        content={"text": content, "data": {}},
        tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
        links={},
        raw={},
    )
    await create_event(payload)
    return await index(request)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

