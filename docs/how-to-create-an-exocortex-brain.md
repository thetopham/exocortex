# How I Created an LLM Wiki Exocortex Brain from My ChatGPT History

This is the simple version of the process I used to turn years of ChatGPT conversations into a local LLM wiki / exocortex brain.

The goal was not to build a perfect knowledge system on day one. The goal was to get my exported ChatGPT history into a browsable markdown wiki that an AI agent could help maintain and improve over time.

The basic loop was:


Download ChatGPT history → create simple wiki skill → run Codex over export files → generate markdown wiki → browse in Obsidian → version with GitHub → improve later


---



## 1. Download All ChatGPT Conversations

First, I downloaded my ChatGPT conversation export.

The export contained my conversations from the last couple of years, split into conversation files such as:

```text
conversation-000.json
conversation-001.json
conversation-002.json
...
```

These files became the raw source material for the exocortex.

The raw files are important because they are the original record. The wiki is the distilled version created from them.

---

## 2. Create a Simple LLM Wiki Skill

I started with Andrej Karpathy’s LLM wiki idea/gist as inspiration.

The process was simple:

1. Download/upload the Karpathy LLM wiki gist or post into ChatGPT.
2. Ask ChatGPT to turn it into a Codex skill.
3. The first version was too complicated.
4. Ask ChatGPT to simplify it.
5. Keep the simplified version as `llm-wiki-skill-v1.md`.

The key lesson was that the skill should be boring and simple.

The AI does not need a huge framework. It needs clear rules:

- keep raw files immutable
- summarize conversations
- create markdown wiki pages
- preserve source dates when possible
- update existing pages instead of creating endless stubs
- keep an index and log
- let the human curate

if you want my version:
- [llm-wiki-skill](docs/llm-wiki-skill-v1.md)
---

## 3. Create the LLM Wiki Brain Folder

I created a local folder for the llm wiki brain.

Example:

```text
brain/
    raw/
      llm-wiki-skill-v1.md
```

At the start, `raw/` was empty.

Then I copied the first ChatGPT export conversation file into it:

```text
brain/raw/conversation-000.json
```

That was enough to begin.

---

## 4. Open Codex in the Brain Folder

Next, I opened the command line inside the llm wiki brain folder and started Codex using my GPT subscription.

The important part was running Codex from the folder that contained the llm wiki brain files.

Example:

```bash
cd brain/
codex
```

Then I set Codex to a stronger reasoning mode:

```text
/model
select gpt-5.5
select xhigh
```

This made the ingest process slower, but more careful.

---

## 5. Tell Codex to Load the Skill and Create the Wiki Structure

Inside Codex, I asked it something like:

```text
Load llm-wiki-skill-v1.md and create the required folders for the wiki.
```

Codex then created the basic structure the skill expected, such as:

```text
raw/
ingest/
wiki/
archive/
wiki/index.md
wiki/log.md
```

The exact folders can vary, but the main idea is:

- `raw/` holds original source files
- `wiki/` holds distilled markdown pages
- `wiki/index.md` helps navigate the wiki
- `wiki/log.md` records what changed

---

## 6. Ingest the First Conversation File

Then I asked Codex:

```text
ingest conversation-000.json
```

Codex read the raw ChatGPT conversation file and generated markdown notes from it.

The output became part of the LLM wiki.

The important thing is that Codex was not just copying the raw conversation. It was distilling it into useful pages: ideas, projects, concepts, issues, decisions, and summaries.

---

## 7. Repeat for Every Conversation File

After the first file worked, I repeated the same process for every exported conversation file:

```text
ingest conversation-001.json
ingest conversation-002.json
ingest conversation-003.json
...
```

Eventually, the full ChatGPT export had been processed.

At that point, I had an LLM wiki containing distilled information from years of conversations: project ideas, technical plans, personal notes, recurring themes, issues, concepts, and decisions.

This became the first real version of the llm wiki exocortex brain.

---

## 8. Browse the Wiki with Obsidian

Because the output is markdown, it can be opened in Obsidian.

That makes the exocortex easy to browse visually with:

- folders
- backlinks
- wiki links
- search
- graph view
- project pages
- daily notes

Obsidian is not required, but it is a good interface for a local markdown llm wiki brain.

---

## 9. Put the LLM Wiki Brain in a Private GitHub Repo

After the wiki existed locally, I created a private GitHub repo for version control.

This gave the exocortex:

- backups
- commit history
- version control
- the ability to sync across machines
- a clean path for AI agents to commit changes later

The repo should stay private if it contains personal ChatGPT history or private notes.

For a public exocortex repo, only publish the method, templates, and sanitized examples — not the raw personal llm wiki brain.
I'd keep it private if it contains anything personal, and years of conversations with gpt probably contains personal info.

---

## 10. Daily Update Workflow

After the initial bulk import, the workflow becomes much simpler.

At the end of the day, I ask ChatGPT to summarize the day’s conversations.

Then I feed that daily summary into the exocortex / LLM wiki.

The daily process is:

```text
Have conversations during the day → ask ChatGPT for daily summary → ingest summary into exocortex → update wiki
```

This prevents the llm wiki brain from becoming stale after the initial export.

Instead of waiting months and doing another huge import, the exocortex can grow a little each day.

---

## 11. What This Creates

After this process, the exocortex contains a distilled memory of years of AI conversations.

It can include:

- project ideas
- open issues
- technical plans
- decisions
- study notes
- recurring themes
- personal workflows
- concepts
- future plans
- tasks
- summaries of old conversations

The raw export is the source archive.

The markdown wiki is the usable exocortex brain.

---

## 12. What Needs Improvement

The current process works, but it can still be improved a lot.

The biggest improvement areas are:

### Better LLM Wiki Skill

The skill should do a better job deciding:

- what becomes a daily note
- what becomes a project page
- what becomes a concept page
- what should only be logged
- when to update an existing page instead of creating a new one

### Better Organization

The wiki needs a cleaner structure for:

- projects
- concepts
- active tasks
- decisions
- daily summaries
- archived ideas
- source references

### Better Source Tracking

Each page should preserve:

- original conversation date
- source file
- ingest date
- update date
- related conversations

This matters because an idea might have been created years before it was ingested into the wiki.

### Better Daily Ingest

The daily summary process should become more repeatable.

Ideally, each day’s summary should extract:

- what happened today
- what changed
- important decisions
- new tasks
- project updates
- memory candidates
- what the AI should remind me about later

### Better Agent Layer

The next layer is having an AI agent read the exocortex and help keep me on track.

That agent could answer:

- What is most important right now?
- What projects have I neglected?
- What did I say I was going to do?
- What should I work on today?
- What ideas are recurring across months or years?
- What should be turned into a real project?

This is the point where the exocortex becomes more than a wiki. 

---

## 13. Minimal Skill Template

This is the kind of simple skill that worked best:

```markdown
---
name: llm-wiki-skill
description: Maintain a simple personal LLM wiki by turning daily inputs into distilled markdown notes.
---

# LLM Wiki Skill — V1

This wiki is a personal exocortex.

The goal is to turn daily ChatGPT summaries, notes, transcripts, and project thoughts into durable markdown memory.

Do not overbuild. Prefer one good daily note over many scattered pages.

## Folder Structure

```text
raw/        -- immutable source files; never edit
ingest/     -- new inputs waiting to be processed
wiki/       -- maintained markdown wiki
archive/    -- old or superseded files
```

Important files:

```text
wiki/index.md
wiki/log.md
```

## Core Rules

1. Never modify files in `raw/`.
2. Preserve source dates separately from ingest dates.
3. Do not copy huge raw conversations into the wiki.
4. Distill inputs into concise durable notes.
5. Do not create lots of new pages unless the user asks.
6. Prefer updating existing pages.
7. Append a short entry to `wiki/log.md` after changes.
8. Update `wiki/index.md` only when creating a new durable page.

## Default Ingest Workflow

When the user asks to ingest a note, summary, transcript, or conversation:

1. Read the input.
2. Identify the source type:
   - daily summary
   - ChatGPT conversation
   - transcript
   - project note
   - research note
   - course note
   - personal reflection
3. Create or update a daily note in `wiki/daily/`.
4. Extract:
   - summary
   - key ideas
   - decisions
   - tasks
   - project updates
   - memory candidates
   - open questions
5. Link to existing pages using `[[page-name]]`.
6. Only create a new project/concept page if the idea is clearly durable.
7. Update `wiki/index.md` if a new durable page was created.
8. Append a short log entry to `wiki/log.md`.

## Daily Note Format

```markdown
# YYYY-MM-DD Daily Note

**Source date**: YYYY-MM-DD or Unknown  
**Ingested date**: YYYY-MM-DD  
**Type**: daily-note

---

## Summary

## Key Ideas

## Decisions

## Tasks

## Project Updates

## Memory Candidates

## Open Questions

## Related Pages
```

## Durable Page Rule

Only create or update a durable page when the input clearly affects:

- a project
- a reusable concept
- a course/study area
- a research area
- a system architecture
- an important decision


## ChatGPT Export Rule

For ChatGPT exports:

1. Keep raw export in `raw/chatgpt/`.
2. Do not create one page per conversation by default.
3. Summarize into themes.
4. Promote only durable ideas into project/concept pages.
5. Keep the wiki cleaner than the raw archive.

## Log Format

Append to `wiki/log.md`:

```markdown
## YYYY-MM-DD

### Ingested
- Source:
- Source date:
- Ingested date:

### Changed
- Created or updated:

### Notes
- Brief explanation.
```

## Style

Use clear, short, plain language.

Avoid:

- giant pages
- over-linking
- unnecessary stubs
- copying raw conversations
- pretending uncertain facts are certain

The human is the curator. The AI is the maintainer.

```

---

## 14. The Simple Version

The whole process can be summarized like this:

```text
1. Export ChatGPT history.
2. Create a simple llm-wiki skill.
3. Create a llm wiki brain folder with raw/ and the skill file.
4. Put the first conversation JSON file in raw/.
5. Open Codex in the llm wiki brain folder.
6. Tell Codex to load the skill and create the wiki folders.
7. Set Codex to xhigh.
8. Ask Codex to ingest conversation-000.json.
9. Repeat for every conversation file.
10. Browse the markdown wiki in Obsidian.
11. Push the private llm wiki brain repo to GitHub for version control.
12. After each day, summarize new ChatGPT conversations and ingest the summary.
13. Push the updated files from your desktop to github for version control. 
14. Later, add an AI agent that references the wiki and helps prioritize what matters.
```

That is the v1 llm wiki exocortex brain.

It is not perfect yet, but it works.

The important part is that years of scattered ChatGPT conversations are no longer trapped in chat history. They become a searchable, editable, version-controlled markdown llm wiki exocortex brain that can compound over time.

15. Next Steps

The next step is to turn the exocortex from just an ai updated wiki into an AI-maintained memory system.

Planned improvements:

1. Give an AI agent access to the private llm wiki exocortex brain repo.
2. Let the agent reference the wiki, project pages, tasks, and daily notes.
3. Create a cron job that runs a daily exocortex update.
4. Automatically summarize the day’s conversations, notes, and events.
5. Ingest the daily summary into the LLM wiki.
6. Commit and push the updated wiki back to the private GitHub repo.
7. Generate a daily brief showing what changed, what matters, and what to do next.
8. Add reminders for neglected projects, stale tasks, and recurring goals.
9. Have the AI give a daily briefing when you wake up about what is important today or any advancements that happen in areas where you are working on stuff, etc.

At that point, the exocortex becomes more than a markdown archive.

It becomes a personal AI sidekick: something that can reference the private brain, maintain continuity, notice patterns, and help keep attention on what matters. 

