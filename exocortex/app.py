from datetime import date, datetime, time
from html import escape
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from .database import EventStore
from .schemas import EventCreate, EventResponse

app = FastAPI(title="Sovereign Exocortex", version="0.0.1")
store = EventStore()


@app.post("/events", response_model=EventResponse)
def create_event(event: EventCreate) -> EventResponse:
    try:
        return store.insert_event(event.dict())
    except ValueError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/events", response_model=List[EventResponse])
def list_events(
    start_time: Optional[datetime] = Query(default=None, description="Start of time range (ISO8601)"),
    end_time: Optional[datetime] = Query(default=None, description="End of time range (ISO8601)"),
    source_system: Optional[str] = Query(default=None, description="Filter by source system"),
    channel: Optional[str] = Query(default=None, description="Filter by channel"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    limit: int = Query(default=100, ge=1, le=500, description="Maximum number of events to return"),
) -> List[EventResponse]:
    return store.fetch_events(
        start_time=start_time,
        end_time=end_time,
        source_system=source_system,
        channel=channel,
        tag=tag,
        limit=limit,
    )


def _render_event(event: EventResponse) -> str:
    tags = ", ".join(event.tags or [])
    content_text = event.content.get("text") if event.content else None
    rows = [
        f"<div class='event'>",
        f"<div class='event-header'><span class='timestamp'>{escape(event.timestamp.isoformat())}</span>"
        f" – <span class='source'>{escape(event.source_system)}</span> / <span class='channel'>{escape(event.channel)}</span></div>",
    ]

    if event.summary:
        rows.append(f"<div class='summary'>{escape(event.summary)}</div>")
    if content_text:
        rows.append(f"<div class='content'>{escape(content_text)}</div>")
    if tags:
        rows.append(f"<div class='tags'>Tags: {escape(tags)}</div>")

    rows.append("</div>")
    return "\n".join(rows)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    events = store.fetch_events(start_time=start, end_time=end, limit=200)

    body = [
        "<html><head><title>Exocortex – Today</title>",
        "<style>body{font-family:Arial, sans-serif; margin:2rem;} .event{padding:1rem;border:1px solid #ddd;",  # noqa: E501
        "border-radius:8px;margin-bottom:1rem;} .event-header{font-weight:bold;} .timestamp{color:#444;}",
        ".source{color:#0b7285;} .channel{color:#1864ab;} .summary{margin-top:0.25rem; font-size:1.05rem;}",
        ".content{margin-top:0.25rem; color:#333;} .tags{margin-top:0.25rem; font-size:0.9rem; color:#555;} form{margin-bottom:1.5rem;}" ,  # noqa: E501
        "label{display:block; margin-bottom:0.25rem;} input[type=text]{padding:0.4rem; width:240px;} button{padding:0.45rem 0.9rem; background:#0b7285; color:white; border:none; border-radius:4px; cursor:pointer;} button:hover{background:#0a5e6b;}" ,  # noqa: E501
        "</style></head><body>",
        "<h1>Exocortex – Today’s Events</h1>",
        "<p>View events for the current day. Use the API for broader queries.</p>",
        "<form method='get' action='/events'>",
        "<label for='source_system'>Source system</label><input name='source_system' id='source_system' type='text' placeholder='e.g. pc_manual'>",
        "<label for='tag'>Tag</label><input name='tag' id='tag' type='text' placeholder='e.g. school'>",
        "<label for='channel'>Channel</label><input name='channel' id='channel' type='text' placeholder='e.g. note'>",
        "<label for='limit'>Limit</label><input name='limit' id='limit' type='text' value='100'>",
        "<button type='submit'>Query /events</button>",
        "</form>",
        "<div class='events'>",
    ]

    if events:
        body.extend(_render_event(event) for event in events)
    else:
        body.append("<p>No events ingested yet today.</p>")

    body.append("</div></body></html>")
    return "".join(body)
