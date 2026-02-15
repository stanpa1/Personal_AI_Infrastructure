# Unified PAI System - Planning Session

**Created:** 2026-01-25
**Status:** brainstorming
**Priority:** medium

---

## Context

Session with Claude exploring how to unify multiple AI tools and add proactive features to PAI. Inspired by ClawdBot architecture and the "Knowledge Loop" project (Gemini conversation about NotebookLM + Google Docs + Claude Code).

---

## Problem Statement

1. **Context fragmentation** - Using Gemini, Claude, ChatGPT, losing track of which app has which conversation
2. **Memory problem** - Many interests and work projects, hard to remember details
3. **2h daily commute** - Want voice interaction during this time
4. **No proactive insights** - System only responds, doesn't initiate

---

## Current Stack (Working)

| Component | Status | Purpose |
|-----------|--------|---------|
| Telegram → PAI inbox | ✅ | Voice, text, @pai triggers |
| Notion | ✅ | Visual dashboard - books, saves, projects |
| Claude Project + Notion MCP | ✅ | Audiobook tracking |
| pai-voice-app | 📋 Planned | Hands-free during commute |
| Morning/evening briefs | ❌ Missing | Proactive insights |

---

## Desired Interaction Model

```
👀 "I want to SEE my projects"      → Notion
💬 "I want to ASK about projects"   → Telegram @pai
🗣️ "I'm driving, hands-free"        → Voice app (parallel to Telegram)
```

---

## Commute Schedule

- **Morning:** 6:30 - 8:30 (flexible)
- **Afternoon:** 16:00 - 19:00 (flexible)

Briefs should arrive BEFORE commute starts.

---

## ClawdBot Comparison

ClawdBot uses:
- WebSocket gateway (real-time)
- Multi-channel inbox (12+ platforms)
- Cron + webhooks for proactive features
- Session isolation

PAI approach:
- HTTP webhooks + batch sync (simpler)
- Telegram-focused
- Same proactive pattern possible (cron + telegram_sender.py)

**Key insight:** Proactivity doesn't require real-time. Cron + triggers = sufficient.

---

## Knowledge Loop Architecture (from Gemini session)

File: `~/Desktop/Aktualizacja-wiedzy-NotebookLM-z-Google-Docs.md`

Architecture for voice-first knowledge management:
```
Gemini Live (voice) → Google Docs → n8n → GitHub → Claude Code → NotebookLM
```

Key concepts:
- **Claude Code as "Lore Keeper"** - checks consistency, detects contradictions
- **Timeline.md** - chronological facts with item status tracking
- **Character Bible** - for book writing projects
- **GitHub versioning** - history of all changes

This could integrate with PAI for project/book knowledge bases.

---

## Proposed Additions

### 1. Proactive Briefs (High priority)

**Morning brief (~6:15):**
- Today's calendar
- Open tasks
- Current audiobook
- Recent saves

**Evening brief (~15:45):**
- Day summary
- Tomorrow preview

Implementation: Python script + cron + `telegram_sender.py`

### 2. Notion MCP on Hetzner

Add to `claude_handler.py` so @pai can:
- Query books database
- Query saves
- Query project status
- Write notes to Notion

### 3. Voice App (Already planned)

pai-voice-app for hands-free commute interaction.
Same backend as Telegram, different input.

### 4. Future: Conversation Unification

Chrome plugin "ChatGPT & AI Backup" already exists.
Future: Chrome MCP for automatic export.
For now: manual exports when needed.

---

## "Where Did I Discuss X?" Solution

| Remember where? | Action |
|-----------------|--------|
| Claude | Check Claude Projects |
| Voice | Telegram history / PAI inbox |
| ChatGPT | Chrome plugin export |
| No idea | Ask @pai (searches PAI + Notion) |

Future: unified search across all sources.

---

## Next Steps (When Ready)

1. [ ] Morning brief script
   - Notion API for calendar/tasks
   - telegram_sender.py for delivery
   - Cron at 6:15

2. [ ] Notion MCP on Hetzner
   - @pai queries Notion directly

3. [ ] pai-voice-app Phase 1
   - Continue existing plan

4. [ ] Evening brief + weekly review
   - After morning brief works

---

## Related Files

- `~/.pai/memory/projects/inbox-system.md` - Current inbox architecture
- `~/.pai/memory/projects/pai-voice-app.md` - Voice app plan
- `~/Desktop/Aktualizacja-wiedzy-NotebookLM-z-Google-Docs.md` - Gemini Knowledge Loop session
- GitHub: clawdbot/clawdbot - Reference architecture

---

## Notes

- Don't overcomplicate - add features incrementally
- Notion = visual, Telegram = conversational, Voice = hands-free
- Proactivity = cron jobs, not real-time complexity
