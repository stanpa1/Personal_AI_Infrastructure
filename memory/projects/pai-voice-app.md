# PAI Voice App

**Status:** phase-2-complete
**Priority:** high
**Created:** 2026-01-24
**Updated:** 2026-02-01

---

## Summary

Voice-controlled interface for PAI using Gemini Live API. Real-time voice conversation with access to PAI memory, projects, and notes.

**Live URL:** https://voice.stankowski.io
**Auth:** pawel / Voicer5757

---

## What's Working (Phase 1)

### Voice Interface
- [x] Real-time voice conversation (Gemini Live API)
- [x] Bidirectional transcription
- [x] Session timer
- [x] Live transcript log
- [x] Multiple voice options (Fenrir, Puck, Charon, etc.)

### PAI Integration
- [x] `searchPAI` - Search memory for past notes, projects
- [x] `getPAIContext` - Get current projects and notes
- [x] `addPAINote` - Save notes to PAI memory
- [x] `queryNotion` - Placeholder for Notion integration

### Infrastructure
- [x] PAI Search API on Hetzner (api.stankowski.io/api/*)
- [x] Production deployment (voice.stankowski.io)
- [x] Basic auth protection
- [x] Voice session storage and search
- [x] HTTPS via Caddy
- [x] Rate limiting (fail2ban: 5 attempts → 1 hour ban)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  PAI Voice (voice.stankowski.io)                            │
│  React + Vite + Gemini Live API                             │
│  Tools: searchPAI, getPAIContext, addPAINote               │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP (tools) + Webhook (session end)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PAI API (api.stankowski.io/api/*)                          │
│  FastAPI + keyword search                                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  PAI Context (/opt/inbox-webhook/pai-context/)              │
│  Projects, notes, voice sessions                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 2 - UI Cleanup ✅ 2026-02-01

- [x] Simplified SetupPanel - big mic button, settings hidden
- [x] Default voice changed to Kore
- [x] System instructions hidden in collapsible menu
- [x] Webhook URL hidden in collapsible menu
- [x] Minimal header (just "PAI" + history icon)
- [x] Cleaner system prompt (no unsolicited info)
- [ ] Add PWA "Add to Home Screen" prompt
- [ ] Test mobile experience further

---

## Phase 2.5 - Notion Project Management ✅ 2026-01-31

- [x] `getProjects` - List projects from Notion
- [x] `updateProject` - Update status/next_action/deadline
- [x] `addProject` - Create new project
- [x] `weeklyReview` - Get weekly review data
- [x] Natural language deadline parsing (Polish & English)
- [x] On-demand weekly review via voice

**New API endpoints:**
- `GET /api/projects` - List projects
- `PATCH /api/projects` - Update project
- `POST /api/projects` - Create project
- `GET /api/weekly-review` - Weekly review data

**Voice commands:**
- "Jakie mam projekty?" → Lists active projects
- "Matryce zrobione" → Marks project as done
- "Ustaw deadline antena na piątek" → Sets deadline
- "Dodaj projekt: zakup laptopa, praca, wysoki" → Creates project
- "Zróbmy weekly review" → Starts weekly review conversation

---

## TODO: Phase 3 - Enhancements

- [ ] Vector database for semantic search (Chroma/pgvector)
- [ ] Calendar integration
- [ ] Proactive context loading at session start

---

## Key Files

**Local source:**
- `/mnt/e/voice/nexus-voice-interface/` - App source
- `/mnt/e/voice/pai_api.py` - API source

**Hetzner:**
- `/var/www/pai-voice/` - Deployed app
- `/opt/inbox-webhook/pai_api.py` - Running API
- `/opt/inbox-webhook/pai-context/inbox/voice-sessions/` - Stored sessions

**Documentation:**
- `/mnt/e/voice/session-2026-01-27-pai-voice-integration.md`
- `/mnt/e/voice/nexus-pai-integration-complete.md`

---

## Technical Notes

- **Model:** gemini-2.5-flash-native-audio-preview
- **Session limit:** ~10-15 minutes
- **Audio:** 16kHz input, 24kHz output, PCM
- **Voice sessions:** Saved on TERMINATE, searchable via API

---

## Related

- unified-pai-system.md - Overall PAI unification plan
- inbox-system.md - Telegram inbox pipeline
