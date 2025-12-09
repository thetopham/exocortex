# Sovereign Exocortex – PRD

## 1. Product Vision

Build a **self-hosted exocortex**: a personal data spine that ingests events from all of Matt’s digital life (notes, emails, workouts, transcriptions, chats, etc.) into a **single timeline** running on a Raspberry Pi, with an AI layer on top that can be queried by voice.

> “Take back my data from the corps, and reconnect my brain so in-person life can tap into the same knowledgebase I had online.”

Long term, this is the prototype of an **Accelerando-style exocortex** for a sovereign individual.

---

## 2. Goals & Non-Goals

### 2.1 Goals (v0 / v1)

1. **Single Timeline of Events**
   - All ingested data is normalized into a unified `Event` model stored on the Pi.
   - Events are queryable by time, tags, source, and basic search.

2. **Self-Hosted, Local-First**
   - Raspberry Pi is the **canonical source of truth**.
   - External services (Gmail, Omi, Health, ChatGPT, etc.) are *inputs/outputs*, not owners.

3. **Simple, Stable Event API**
   - A minimal HTTP API (`/events`, `/events?filters`) that all connectors can talk to.
   - Clear JSON schema so future tools & agents can read/write events without changes.

4. **Initial Data Connectors**
   - At least **3 real sources** wired in end-to-end for v1:
     - Manual notes (PC / S25+)
     - Omi transcriptions (via whatever integration is easiest)
     - One primary email account (Gmail or school email)

5. **Human-Usable UI**
   - Web page(s) to:
     - View today’s events
     - Filter by tag & source
     - Manually add simple notes

### 2.2 Later Goals (v2+)

- AI query agent (“Ask my exocortex”) with natural language Q&A.
- Semantic/vector search over events.
- Voice loop via Omi / S25+ (speak → query → answer).
- Additional connectors: Galaxy Health, Freeletics, SMS, call logs, more email accounts, full ChatGPT/Gemini history.

### 2.3 Non-Goals (for now)

- No real-time *continuous* recording of all screen/audio like Windows Recall.
- No multi-user exocortex (this is **single-human only**).
- No complex, multi-agent orchestration (just a single AI process on top).
- No perfect historical backfill — selective imports are acceptable.

---

## 3. Users & Use Cases

### 3.1 Primary User

**Matt** – hermit developer / CS student / idea factory.  
Wants his AI-augmented mind back, but controlled locally.

### 3.2 Core Use Cases

**UC-1: Daily Life Logging**
- While studying, walking Odin, or doing theorycrafting, Matt sends notes to the exocortex:
  - “Note: idea for xyz.”
  - “Task: email professor about extra credit.”
  - Omi transcribes a walk conversation and it becomes events.

**UC-2: Recalling Context Before Events**
- Before a CSCI 3308 exam:
  - Query: “Show all events tagged `csci3308` from the last 2 weeks.”
- Before a meeting:
  - Query: “What did I last say about xyz feature?”

**UC-3: Email Context**
- Query: “Summarize my school emails from the last 3 days.”
- Query: “What were the key deadlines mentioned in emails tagged `csci3308` last month?”

**UC-4: Physical + Cognitive Correlation**
- Later: explore correlations like:
  - “How did my step count and Freeletics workouts trend vs. big school deadlines?”
  - “Summarize this semester’s health + workload data.”

**UC-5: AI as Memory Interface**
- Eventually:
  - Matt asks via voice: “What tasks did I mention yesterday related to exocortex v0?”
  - AI answers, referencing the exocortex events.

---

## 4. Scope by Version

### 4.1 v0 – ExoCore Spine

- Minimal event model defined & implemented.
- Pi service with:
  - `POST /events`
  - `GET /events` (time range + filters)
- SQLite (or similar) for persistence.
- Simple HTML “Today’s Events” list.

**Success Criteria v0:**
- Matt can manually POST notes (via a CLI or small script) and see them appear in the UI.
- Data survives reboots and is reasonably easy to back up.

---

### 4.2 v1 – Real Connectors & Usable Timeline

Add **three** real-world connectors:

1. **Manual Notes Connector**
   - From PC & S25+:
     - Some way to “Share to Exocortex” → POST /events.
   - Could be:
     - A Python CLI, or
     - An Android HTTP-shortcut, etc.

2. **Omi Connector**
   - Use whichever path is easiest:
     - Omi → Notion (or other) → scheduled sync script → Exocore
     - or Omi → share text → Exocore
   - Each Omi transcription/summary becomes one or more events.

3. **Email Connector (one account)**
   - Script that pulls new messages every N minutes.
   - Normalizes them into events (subject, from, to, snippet, labels).

Also:

- Upgrade UI:
  - Filter by `source_system` and `tags`.
  - Show basic pagination and timestamps.

**Success Criteria v1:**
- At least 1 week of real data from notes + Omi + email visible and queryable.
- Matt can answer questions like “What did I log about xyz this week?” by browsing the UI (AI is not required yet).

---

### 4.3 v2 – AI Query Layer (MVP)

- A simple AI “query endpoint” that:
  - Accepts a natural language question.
  - Translates it into search over events.
  - Summarizes results using an LLM (OpenAI or local).
- Basic relevance heuristic (by time, tag, keyword).

**Stretch:**
- Very basic voice loop:
  - Use phone/PC for STT and TTS as a prototype.

**Success Criteria v2:**
- Matt can type into a chat UI:
  - “What did I say about exocortex architecture yesterday?”
- Gets a coherent answer that references actual events from Exocore.

---

## 5. Requirements

### 5.1 Functional

- The system **must**:
  1. Ingest events via HTTP in a standard JSON format.
  2. Persist events on the Pi.
  3. Allow retrieval of events filtered by:
     - time range
     - source_system
     - channel
     - tags (basic)
  4. Provide a web UI to:
     - see events for today,
     - filter by tags/source,
     - add a manual note event.

### 5.2 Non-Functional

- **Local-first & Offline-friendly**
  - The Pi must function even if the internet is down (for local logging & retrieval).
- **Security**
  - Expose the API only on LAN initially.
  - Require at least a simple token for programmatic access.
- **Performance**
  - Target scale: up to tens/hundreds of thousands of events without becoming unusable.
- **Portability**
  - Code should be portable enough to run on a normal Linux box or container later.

---

## 6. Open Questions

- How much historical backfill to tackle early (e.g., ChatGPT archives, old emails)?
- SQLite vs. Postgres on Pi for long-term scaling?
- Which vector DB (if any) to adopt in v2 (Qdrant, Chroma, etc.)?
- How tightly to couple the AI layer to Exocore (same process vs. separate service)?

---

## 7. Risks & Mitigations

- **Over-scoping connectors**
  - Mitigation: limit v1 to 3 sources max.
- **Security / privacy**
  - Mitigation: LAN-only, token-based access, encrypted backups.
- **Fragmented dev focus**
  - Mitigation: always prioritize core spine stability over new connectors.

---

## 8. Future Directions

- Multi-device “thick clients” for:
  - Omi / AR HUD,
  - Watch (glanceable stats, tasks),
  - Desktop (rich timeline UI).
- Advanced agents:
  - nightly summarizer,
  - task extractor,
  - anomaly/mood detector based on text + health data.
- Open-source release (event schema + reference implementation) for other sovereign individuals.
