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
