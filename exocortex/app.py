import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .db import get_connection, init_db, serialize_tags
from .models import Event, EventCreate, EventInsert

app = FastAPI(title="Sovereign Exocortex")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@app.on_event("startup")
def startup_event() -> None:
    init_db()


def fetch_events(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[Event]:
    conn = get_connection()
    query = "SELECT * FROM events WHERE 1=1"
    params: list[Any] = []

    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time.isoformat())
    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time.isoformat())
    if source_system:
        query += " AND source_system = ?"
        params.append(source_system)
    if channel:
        query += " AND channel = ?"
        params.append(channel)
    if tags:
        for tag in tags:
            query += " AND tags LIKE ?"
            params.append(f"%{tag.lower()}%")

    query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [Event.from_row(dict(row)) for row in rows]


@app.post("/events")
def create_event(event: EventCreate) -> dict:
    conn = get_connection()
    event_id = EventInsert.build_id()
    ingested_at = datetime.now(timezone.utc).isoformat()

    content_json = json.dumps(event.content.data)
    tags_text = serialize_tags(event.tags)
    links_json = json.dumps(event.links.dict(exclude_none=True))
    raw_json = json.dumps(event.raw)

    conn.execute(
        """
        INSERT INTO events (
            id, timestamp, source_system, channel, actor, direction, summary,
            content_text, content_json, tags, links_json, raw_json, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event_id,
            event.timestamp.isoformat(),
            event.source_system,
            event.channel,
            event.actor,
            event.direction,
            event.summary,
            event.content.text,
            content_json,
            tags_text,
            links_json,
            raw_json,
            ingested_at,
        ),
    )
    conn.commit()
    conn.close()
    return {"id": event_id, "status": "ok"}


@app.get("/events", response_model=List[Event])
def list_events(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    source_system: Optional[str] = None,
    channel: Optional[str] = None,
    tags: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[Event]:
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()] if tags else None
    return fetch_events(start_time, end_time, source_system, channel, tag_list, limit, offset)


@app.get("/", response_class=HTMLResponse)
def timeline_page(request: Request, source_system: Optional[str] = None, tags: Optional[str] = None) -> HTMLResponse:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()] if tags else None
    events = fetch_events(today_start, today_end, source_system=source_system, tags=tag_list, limit=200)
    unique_sources = sorted({e.source_system for e in events})
    all_tags = sorted({tag for e in events for tag in e.tags})
    return templates.TemplateResponse(
        "timeline.html",
        {
            "request": request,
            "events": events,
            "source_system": source_system or "",
            "tags": tags or "",
            "available_sources": unique_sources,
            "available_tags": all_tags,
        },
    )


@app.post("/ui/events")
def create_event_from_form(
    request: Request,
    summary: str = Form(...),
    content_text: str = Form(""),
    source_system: str = Form("manual_note"),
    tags: str = Form(""),
) -> RedirectResponse:
    if not summary.strip():
        raise HTTPException(status_code=400, detail="Summary is required")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    create_event(
        EventCreate(
            timestamp=datetime.now(timezone.utc),
            source_system=source_system,
            channel="note",
            actor="matt",
            direction="outbound",
            summary=summary,
            content={"text": content_text, "data": {}},
            tags=tag_list,
            links={},
            raw={},
        )
    )
    return RedirectResponse(url=str(request.url_for("timeline_page")), status_code=303)
