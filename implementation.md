# Sovereign Exocortex – Implementation Plan

## 1. Architecture Overview

### 1.1 High-Level Components

- **Exocortex (Pi)**
  - HTTP API (`/events`, `/events` GET)
  - Event store (SQLite for v0/v1)
  - Minimal Web UI (timeline + filters)

- **Connectors**
  - Small scripts/services that:
    - fetch from external systems,
    - normalize to the Event schema,
    - POST to exocortex.

- **AI Layer (v2+)**
  - Service that:
    - reads from exocortex,
    - performs search/filter,
    - calls LLM to answer questions,
    - (optionally) writes notes/memories back as events.

- **Clients**
  - CLI tools (PC),
  - phone shortcuts (S25+),
  - Omi sharing,
  - browser UI.

---

## 2. Data Model

### 2.1 Event Schema (Logical)

Core event shape:

```jsonc
{
  "id": "uuid",
  "timestamp": "2025-12-09T15:23:11-07:00",
  "source_system": "gmail_school",   // "omi" | "watch" | "phone_sms" | "chatgpt" | ...
  "channel": "email",                // "voice_transcript" | "workout" | "call" | "sms" | "ai_conversation" | ...
  "actor": "matt",                   // or outside contact
  "direction": "inbound",            // "outbound" | "system"
  "summary": "Short human summary",
  "content": {
    "text": "Optional long text content",
    "data": {}                       // JSON for structured fields per source
  },
  "tags": ["school", "csci3308"],
  "links": {
    "external_url": null,
    "app": null
  },
  "raw": {}                          // optional: full source payload
}
```

### 2.2 Suggested SQLite Schema (v0/v1)

```sql
CREATE TABLE events (
    id           TEXT PRIMARY KEY,       -- UUID
    timestamp    TEXT NOT NULL,          -- ISO8601 string
    source_system TEXT NOT NULL,
    channel      TEXT NOT NULL,
    actor        TEXT,
    direction    TEXT,
    summary      TEXT,
    content_text TEXT,                   -- quick access to full text
    content_json TEXT,                   -- JSON string for content.data
    tags         TEXT,                   -- comma-separated or JSON
    links_json   TEXT,                   -- JSON for links
    raw_json     TEXT,                   -- original payload if desired
    ingested_at  TEXT NOT NULL           -- server timestamp
);

CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_events_source ON events(source_system);
CREATE INDEX idx_events_channel ON events(channel);
CREATE INDEX idx_events_tags ON events(tags);
```

Later, you can add:

- FTS virtual table for `content_text` + `summary`.
- Separate tables for `tasks`, `memories` if needed.

---

## 3. exocortex Service (Pi)

### 3.1 Tech Stack (v0 Recommendation)

- **Language:** Python  
- **Web Framework:** FastAPI or Flask (FastAPI recommended for clean typing)  
- **DB:** SQLite via SQLAlchemy/`sqlite3`

### 3.2 API Endpoints

#### `POST /events`

- **Request body:** Event JSON without `id`/`ingested_at` (server fills those).
- **Server behavior:**
  - Validate required fields:
    - `timestamp`, `source_system`, `channel`.
  - Generate UUID `id`.
  - Set `ingested_at` to current time.
  - Normalize tags to a canonical representation (e.g. comma-separated lowercase).
  - Insert into DB.
- **Response:**
  ```json
  {
    "id": "generated-uuid",
    "status": "ok"
  }
  ```

#### `GET /events`

- **Query params (optional):**
  - `from` (ISO8601 datetime or date)
  - `to`
  - `source_system`
  - `channel`
  - `tag` (single tag for now)
  - `limit` (default 50, max 500)
- **Behavior:**
  - Build SQL query with WHERE clauses.
  - Return events sorted by `timestamp` descending by default.
- **Response:**
  ```json
  {
    "events": [ { ...event... }, ... ]
  }
  ```

#### (Optional v1) `GET /events/{id}`

- Return a single event, including all JSON fields.

---

## 4. Web UI

### 4.1 Minimal Requirements (v0/v1)

- Simple HTML (no framework required at first) served from same app:
  - `/` → “Today’s Events” page
- Features:
  - List events (summary, timestamp, source, tags).
  - Filter form:
    - date range (from/to)
    - source_system dropdown
    - channel dropdown
    - tag input
  - Manual “Add Note” form:
    - textarea for text
    - tags input
    - hidden or preset source_system = `manual`
    - POSTs to `/events`.

Later, you can upgrade to:

- React/Vue/htmx frontend.
- Better timeline visualization.

---

## 5. Connectors (v1)

Aim: build one connector at a time, each as a small, testable script or micro-service.

### 5.1 Manual Notes Connector (PC & S25+)

**PC CLI (Python example):**

- Command:  
  ```bash
  exo-note "My note text" --tags csci3308,idea
  ```
- Behavior:
  - Build event:
    - `source_system = "pc_manual"`
    - `channel = "note"`
    - `actor = "matt"`
    - `direction = "outbound"`
    - `summary = first 80 chars or user-provided`
    - `content.text = full note`
  - POST to `http://pi.local:PORT/events`.

**S25+ Shortcut:**

- Use an HTTP shortcut app / custom Android app:
  - “Share to Exocortex” endpoint.
  - Takes selected text, prompts for tags, POSTs to `/events`.

---

### 5.2 Omi Connector

**Phase 1 (easiest path):**

- Let Omi write to a third-party (e.g., Notion).
- Write a scheduled script (run on Pi or PC) that:
  - Calls Notion API to fetch new pages/entries tagged `exocortex`.
  - For each:
    - Extract:
      - text content,
      - timestamps,
      - maybe session metadata.
    - Build event with:
      - `source_system = "omi"`
      - `channel = "voice_transcript"`
      - `content.text = transcription/summary`
      - appropriate tags.
    - POST to `/events`.

**Phase 2 (direct path):**

- If Omi supports HTTP/webhook actions or share intents:
  - Configure it to send transcription text directly to your `/events` endpoint via your phone.

---

### 5.3 Email Connector (Gmail/School)

**Implementation outline:**

- Run a Python script on PC or Pi:
  - Uses Gmail API (OAuth) for one account.
  - Polls new messages every N minutes (or just manually triggered for v1).
  - For each new message:
    - Extract:
      - `date`, `from`, `to`, `subject`, labels, snippet/body.
    - Build event:
      - `source_system = "gmail_personal"` / `"gmail_school"`
      - `channel = "email"`
      - `actor = sender_name_or_email`
      - `direction = "inbound"` (for received mail)
      - `summary = subject`
      - `content.text = snippet or body`
      - `content.data = {subject, from, to, labels}`

- Keep a small local state (e.g. last synced message ID) to avoid duplicates.

---

## 6. AI Query Layer (v2 Outline)

### 6.1 Service Responsibility

- Expose `/ask` endpoint:
  - Input:
    ```json
    {
      "question": "What did I say about exocortex architecture yesterday?"
    }
    ```
  - Flow:
    1. Interpret question → search filters (time, tags, keywords).
    2. Call exocortex `/events` (and later `/search`) to retrieve relevant events.
    3. Build prompt for LLM with:
       - question,
       - selected event snippets,
       - instructions to answer using only this data.
    4. Return summarized answer + references to event IDs.

- Output:
  ```json
  {
    "answer": "...",
    "used_event_ids": ["...", "..."]
  }
  ```

### 6.2 Implementation

- Can run on the Pi (small models) or on the 3080 PC (preferred for heavier LLMs).
- Use OpenAI API at first for simplicity, then consider local models later.

---

## 7. Security & Deployment

### 7.1 Network

- Run exocortex on Pi, bound to LAN IP.
- Use non-default port (e.g. 8081).
- For v0, accept requests only from local network.

### 7.2 Auth

- v0: simple shared secret token in header:
  - `Authorization: Bearer <EXO_TOKEN>`
- All connectors must include the token.

### 7.3 Backups

- Nightly cron job:
  - Dump SQLite DB to timestamped file.
- Store backup in:
  - another disk,
  - optionally cloud storage (encrypted).

---

## 8. Milestones

### Milestone 1: exocortex Skeleton

- [ ] SQLite schema created.
- [ ] FastAPI/Flask server running on Pi.
- [ ] `POST /events` & `GET /events` working.
- [ ] Very basic HTML listing for today’s events.

### Milestone 2: Manual Connector

- [ ] PC CLI tool to post notes.
- [ ] Test multiple notes per day.
- [ ] Basic tags & filtering in UI.

### Milestone 3: Omi Connector

- [ ] Chosen integration path (Notion or direct share).
- [ ] Script to sync Omi entries → events.
- [ ] At least one day’s worth of Omi events visible in exocortex.

### Milestone 4: Email Connector

- [ ] Gmail API auth set up.
- [ ] Script to import today’s emails as events.
- [ ] Ability to filter events by `source_system = gmail_*` in UI.

### Milestone 5: AI Prototype (Optional for now)

- [ ] Simple `/ask` service querying exocortex.
- [ ] One Q&A example working end-to-end in a terminal/web form.

---

## 9. Nice-to-Haves / Future

- Task extraction job:
  - scan events for “Task:” prefix and store tasks separately.
- Daily digest generator:
  - summarize all events tagged `school` or `project:*` into a nightly summary event.
- Health/time correlation dashboards:
  - Grafana or simple charts over event data.
