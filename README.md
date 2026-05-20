## Guides

5/5/26 most recent version here ->
- [How I Created an Exocortex Brain from My ChatGPT History](docs/how-to-create-an-exocortex-brain.md)

original idea:
# 🧠 Sovereign Exocortex 

> _“We’re taking back our data from the corps and empowering the sovereign individual.”_

Sovereign Exocortex is a self-hosted _personal data spine_ running on a Raspberry Pi.

It ingests events from all parts of your life — notes, emails, workouts, transcriptions, AI chats, etc. — into a **single timeline** with a stable API. Later, an AI layer can sit on top of this timeline to answer questions like:

- _“What did I say about xyz last week while walking Odin?”_  
- _“Summarize my school emails and tasks from the last 3 days.”_  
- _“What were the key ideas from my exocortex planning chats?”_

Right now, the focus is **data plumbing**: centralizing everything on the Pi so future AI can index and reason over it.

---

## 🚀 Project Goals

1. **Single Timeline of Events**  
   Everything becomes a normalized `Event` stored on the Pi, queryable by time, tags, and source.

2. **Self-Hosted & Local-First**  
   The Raspberry Pi is the **canonical source of truth**. Cloud tools are inputs/outputs, not owners.

3. **Simple, Stable Event API**  
   A minimal HTTP API (`/events` for write, `/events` for read) that all connectors speak.

4. **Incremental Connectors**  
   Start small (manual notes, Omi, one email account), then layer in more sources over time.

5. **AI-Ready (Later)**  
   Once the data spine is stable, add an AI layer that can search, summarize, and answer questions over your event stream.

---

## 🧩 High-Level Architecture

- **exocortex (Pi)**
  - HTTP API for events.
  - SQLite event store (v0/v1).
  - Minimal web UI for browsing/filtering the timeline.

- **Connectors**
  - Small scripts/services that:
    - fetch from sources (Omi, Gmail, health, ChatGPT exports, etc.),
    - map to the `Event` schema,
    - `POST` to exocortex.

- **AI Layer (v2+)**
  - A separate service that:
    - queries exocortex for relevant events,
    - calls an LLM (OpenAI/local),
    - returns answers (and optionally logs new events/memories).

- **Clients**
  - CLI tools.
  - Android “Share to Exocortex” shortcuts.
  - Omi apps.
  - Browser UI.

---

## 🧱 Event Model (Conceptual)

All data is normalized to a single `Event` shape:

```jsonc
{
  "id": "uuid",
  "timestamp": "2025-12-09T15:23:11-07:00",
  "source_system": "gmail_school",   // "omi" | "watch" | "phone_sms" | "chatgpt" | ...
  "channel": "email",                // "voice_transcript" | "workout" | "call" | "sms" | "ai_conversation" | ...
  "actor": "matt",
  "direction": "inbound",            // "outbound" | "system"
  "summary": "Short human summary",
  "content": {
    "text": "Optional long text content",
    "data": {}                       // structured fields per source
  },
  "tags": ["school", "csci3308"],
  "links": {
    "external_url": null,            // link back to original item
    "app": null                      // deep link, if any
  },
  "raw": {}                          // optional full source payload
}
```

Internally this is stored in SQLite (v0/v1) with JSON/text columns for flexible evolution.

---

## 📦 Current Scope

### v0 – exocortex Spine

- [x] FastAPI server running on the Pi.
- [x] SQLite `events` table + basic indexes.
- [x] `POST /events` – ingest events.
- [x] `GET /events` – list/filter events.
- [x] Simple HTML “Today’s Events” view.

#### Running v0 locally

1. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Initialize the SQLite database (creates `exocortex/exocortex.db`):

   ```bash
   python scripts/init_db.py
   ```

3. Launch the server:

   ```bash
   uvicorn exocortex.app:app --host 0.0.0.0 --port 8081
   ```

4. POST an event:

   ```bash
   curl -X POST http://localhost:8081/events \
     -H "Content-Type: application/json" \
     -d '{
       "timestamp": "2025-12-09T15:23:11-07:00",
       "source_system": "pc_manual",
       "channel": "note",
       "actor": "matt",
       "direction": "outbound",
       "summary": "First sovereign exocortex test event",
       "content": { "text": "Hello from exocortex", "data": {} },
       "tags": ["exo", "test"],
       "links": { "external_url": null, "app": null },
       "raw": {}
     }'
   ```

5. Open `http://localhost:8081/` to see today’s events rendered in the timeline.

### v1 – Real Connectors

First three connectors:

1. **Manual Notes (PC + S25+)**
   - CLI tool (PC) and/or Android HTTP shortcut to send text → `/events`.

2. **Omi Transcriptions**
   - Easiest integration path (e.g. Omi → Notion → sync script → exocortex).

3. **One Email Account**
   - Gmail/school email polling → normalize to events.

### v2 – AI Query Layer (Future)

- `/ask` endpoint that:
  - interprets a natural language question,
  - searches/filter events,
  - uses an LLM to answer,
  - returns answer + referenced event IDs.

---

## 🛠 Getting Started (Dev Notes)

> _This section is a living checklist for setting up on the Pi._

### Requirements

- Raspberry Pi (with at least ~256 GB storage)
- Python 3.x
- SQLite
- `pip` for Python deps

### Setup (rough sketch)

1. Clone the repo:

   ```bash
   git clone <your-repo-url> exocortex
   cd exocortex
   ```

2. Create and activate a virtualenv:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   ```

3. Install dependencies (to be defined):

   ```bash
   pip install fastapi uvicorn sqlite-utils
   ```

4. Initialize the database:

   ```bash
   python scripts/init_db.py
   ```

5. Run the server:

   ```bash
   uvicorn exocortex.app:app --host 0.0.0.0 --port 8081
   ```

6. Send a manual note from your PC:

   ```bash
   python scripts/manual_note_cli.py "Walk idea: voice UI" \
     --text "Try a push-to-talk shortcut that posts transcripts" \
     --tags exo,idea,walk
   ```

   The CLI defaults to posting to `http://localhost:8081/events` with `source_system=manual_pc` and `channel=note`. Use `--api-url` to target a remote Pi.

7. Test a manual event:

   ```bash
   curl -X POST http://pi.local:8081/events \
     -H "Content-Type: application/json" \
     -d '{
       "timestamp": "2025-12-09T15:23:11-07:00",
       "source_system": "pc_manual",
       "channel": "note",
       "actor": "matt",
       "direction": "outbound",
       "summary": "First sovereign exocortex test event",
       "content": { "text": "Hello from exocortex", "data": {} },
       "tags": ["exo", "test"],
       "links": { "external_url": null, "app": null },
       "raw": {}
     }'
   ```

Then open the web UI (e.g. `http://pi.local:8081/`) to confirm the event appears and use the filters at the top to narrow by time, source, channel, or tag.

---

## 📂 Suggested Repo Structure

```text
.
├─ README.md
├─ docs/
│  ├─ prd.md
│  └─ implementation.md
├─ exocortex/
│  ├─ app.py            # FastAPI/Flask entrypoint
│  ├─ models.py         # Event model / DB schema
│  ├─ db.py             # DB connection & migration helpers
│  ├─ routes.py         # /events, UI routes
│  ├─ templates/        # HTML templates for timeline UI
│  └─ static/           # CSS/JS (if needed)
├─ connectors/
│  ├─ manual_note_cli/
│  ├─ omi_sync/
│  ├─ gmail_sync/
│  └─ ...
└─ scripts/
   ├─ init_db.py
   └─ dev_utils.py
```

---

## 🗺 Roadmap (High Level)

- **v0:** exocortex spine + manual event posting.
- **v1:** Connectors for notes, Omi, email; usable timeline UI.
- **v2:** AI query layer (`/ask`) + basic semantic search.
- **v3+:**
  - Health/workout data integration.
  - Phone call/SMS logs.
  - Task extraction + daily digests.
  - Voice loop via Omi / S25+.
  - Open-sourcing the exocortex schema + reference implementation.

---

## 🧑‍💻 Contributing

Right now this is a **personal project** for building a real-world exocortex prototype.  
Future you (or others) may turn it into an open-source template for sovereign individuals.

For now:

- Keep `docs/prd.md` and `docs/implementation.md` in sync with reality.
- Add new connectors under `connectors/` as small, composable scripts.
- Prefer boring, transparent design over cleverness — this is your brain, not a hackathon demo.

---

## ⚖️ License

_TBD_


