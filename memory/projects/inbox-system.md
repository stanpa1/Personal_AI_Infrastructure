# Inbox System - Project Status

**Last Updated:** 2026-02-14 22:30
**Status:** FAZA 4.5 Complete - Voice App Inbox Access

**Repositories:**
- PAI Infrastructure: https://github.com/stanpa1/Personal_AI_Infrastructure
- Voice App: https://github.com/stanpa1/pai-voice-app

---

## Overview

Voice-first, mobile-first personal knowledge capture system. Captures Telegram messages (voice/photo/text) and processes them into PAI memory.

## Architecture

```
Telegram → n8n → Google Drive
                      ↓
              n8n webhook POST
                      ↓
        https://api.stankowski.io/hook/n8n
                      ↓
           /opt/inbox-webhook/queue/
                      ↓
              worker.py processes
                      ↓
           /opt/inbox-webhook/downloads/
                      ↓
              rsync to local
                      ↓
           ~/.pai/inbox/raw/
                      ↓
           InboxProcessor skill
                      ↓
           ~/.pai/memory/
```

---

## Server Components (Hetzner: 157.180.26.47)

### Services

| Service | Port | Status | Description |
|---------|------|--------|-------------|
| `inbox-webhook.service` | 8010 | ✅ Running | FastAPI webhook receiver |
| `inbox-worker.service` | - | ✅ Running | Queue processor (2s polling) |
| `pai-api.service` | 8001 | ✅ Running | PAI Search API (voice app backend) |
| `fastapi.service` | 8000 | ✅ Running | Main API (api.stankowski.io) |
| `caddy` | 443 | ✅ Running | HTTPS reverse proxy |

### File Locations

```
/opt/inbox-webhook/
├── main.py              # FastAPI webhook (port 8010)
├── worker.py            # Queue processor
├── process_event.py     # Event handler (MVP - metadata only)
├── .env                 # WEBHOOK_SECRET
├── venv/                # Python virtualenv
├── queue/               # Incoming events
├── processing/          # Currently processing
├── done/                # Completed
├── failed/              # Errors
└── downloads/           # Event data + metadata
    └── <event_id>/
        └── metadata.json
```

### Endpoints

- `https://api.stankowski.io/hook/n8n` - Webhook endpoint
  - Method: POST
  - Header: `X-Webhook-Secret: <secret>`
  - Body: InboxEvent JSON

### Webhook Secret

```bash
ssh hetzner "grep WEBHOOK_SECRET /opt/inbox-webhook/.env | cut -d= -f2"
```

### Management Commands

```bash
# Status
ssh hetzner "systemctl status inbox-webhook inbox-worker"

# Logs
ssh hetzner "journalctl -u inbox-worker -f"

# Restart
ssh hetzner "systemctl restart inbox-webhook inbox-worker"

# Queue stats
ssh hetzner "echo 'Queue:' && ls /opt/inbox-webhook/queue/*.json 2>/dev/null | wc -l && echo 'Done:' && ls /opt/inbox-webhook/done/*.json 2>/dev/null | wc -l"
```

---

## Local Components (WSL/PAI)

### File Locations

```
~/.pai/inbox/
├── raw/            # Synced from server (rsync)
├── processed/      # After Claude processing
└── archive/        # Old events (>30 days)

~/.pai/sync-inbox.sh           # Sync script
~/.claude/skills/InboxProcessor/SKILL.md  # Processing skill
```

### Sync Command

```bash
~/.pai/sync-inbox.sh
# Or manually:
rsync -avz hetzner:/opt/inbox-webhook/downloads/ ~/.pai/inbox/raw/
```

---

## Progress Tracking

### FAZA 1 - MVP ✅ COMPLETE

- [x] FastAPI webhook endpoint with auth
- [x] File-based queue system (queue/ → processing/ → done/)
- [x] Worker with 2-second polling
- [x] Event processing (metadata only)
- [x] Systemd services with auto-restart
- [x] HTTPS via Caddy reverse proxy
- [x] Idempotency check (duplicate rejection)
- [x] Structured logging
- [x] Local PAI integration (inbox/ directory)
- [x] Sync script (sync-inbox.sh)
- [x] InboxProcessor skill scaffold

### FAZA 2 - COMPLETE ✅ 2026-01-18

- [x] Google Drive API integration ✅ 2026-01-18
  - Service Account: pai-inbox-worker@pai-inbox.iam.gserviceaccount.com
  - Credentials: /opt/inbox-webhook/credentials.json
  - Shared folder: Telegram_Files
  - Worker auto-downloads files from GDrive
- [x] Audio transcription (Whisper API) ✅ 2026-01-18
  - Uses OpenAI Whisper API
  - OPENAI_API_KEY in ~/.pai/.env
- [x] Image OCR/description (GPT-4 Vision) ✅ 2026-01-18
  - Uses GPT-4o Vision API
  - Extracts description + OCR text
- [ ] Auto-sync (inotify/watchdog) - optional
- [x] n8n webhook already configured

### FAZA 2.5 - Bidirectional Communication ✅ 2026-01-18

- [x] `@pai` trigger detection in messages
- [x] DeepSeek API integration (cost-effective)
- [x] PAI context sync to server (cron every 2h, 8:00-22:00)
- [x] Context loading: telos, projects, short-term notes
- [x] Telegram Bot response sender
- [x] Voice message transcription + AI response

**New files on server:**
- `/opt/inbox-webhook/telegram_sender.py`
- `/opt/inbox-webhook/claude_handler.py`
- `/opt/inbox-webhook/pai-context/` (synced from local)

**Bidirectional sync:**
- `~/.pai/sync-pai-context.sh` - PC → Hetzner (cron co 2h, 8:00-22:00)
- `~/.pai/sync-from-hetzner.sh` - Hetzner → PC (auto przy starcie sesji)
- Hook: `initialize-session.ts` wywołuje sync przy każdej sesji Claude

### FAZA 2.6 - Notion Integration ✅ 2026-01-28

- [x] Notion MCP configured (Claude.ai hosted)
- [x] Note List database connected (ID: 9d5a78f7-c14e-44f8-b885-8cc5feaf99f8)
- [x] Weekly Digest generator working
- [x] First digest saved to Notion
- [x] NotionDigest skill created (`~/.claude/skills/NotionDigest/`)
- [x] NotionAutoType skill created (`~/.claude/skills/NotionAutoType/`)
- [x] Scripts copied to `~/.pai/scripts/notion/`
- [x] Cron job: Sunday 20:00 weekly digest reminder

**Skills created:**
- `NotionDigest` - "wygeneruj weekly digest"
- `NotionAutoType` - "dodaj do notion: [treść]"

**Scripts location:** `~/.pai/scripts/notion/`
- `weekly-digest.py`
- `link-content-fetcher.py`
- `generate-digest.sh`

### FAZA 3 - PAI Planner ✅ 2026-01-31

- [x] PAI migrated to Hetzner (24/7 availability)
- [x] Node.js + Claude Code installed on server
- [x] Projects database in Notion (5 test projects)
- [x] Notion API integration (direct, not MCP)
- [x] DeepSeek AI for message generation
- [x] Daily check-ins: 6:30 morning, 19:00 evening
- [x] Cron jobs configured
- [x] Telegram notifications working

**New files on server:**
- `/root/.pai/` - Full PAI installation
- `/root/.pai/scripts/planner/checkin.py` - Check-in logic
- `/etc/cron.d/pai-checkin` - Scheduled jobs

**Documentation:** `~/.pai/memory/projects/pai-planner.md`

### FAZA 3.1 - Response Processing ✅ 2026-01-31

- [x] Parse user responses to update Notion
- [x] Detect status updates ("done", "zrobione")
- [x] Add new projects via Telegram ("dodaj projekt:")
- [x] Update next action ("update X: nowa akcja")
- [x] Fuzzy project name matching
- [x] Natural language deadline parsing (Polish & English)
- [x] Weekly review (Sunday 19:00)

**New files on server:**
- `/opt/inbox-webhook/notion_project_handler.py` - Intent detection & Notion updates

**Usage examples:**
```
"antena gsm - zrobione"           → Marks project as Done
"update matryce: spotkanie jutro" → Updates Next Action
"dodaj projekt: nowy task, praca" → Creates new project
"deadline antena: do piątku"      → Sets deadline to next Friday
"termin matryce: 15 lutego"       → Sets deadline to Feb 15
"przesuń antena na za tydzień"    → Moves deadline by 1 week
```

**Supported deadline formats:**
- Relative: jutro, pojutrze, za X dni, za tydzień, za miesiąc
- Days: do piątku, w poniedziałek, friday, next monday
- Dates: 15 lutego, 15.02, february 15, 2026-02-15
- Special: koniec tygodnia, koniec miesiąca, weekend

**Weekly Review (Sunday 19:00):**
- Podsumowanie ukończonych projektów
- Lista aktywnych projektów z priorytetami
- Wykrywanie projektów bez przeglądu >7 dni
- Deadline'y na nadchodzący tydzień
- Pytania do refleksji

**Cron schedule:**
- Morning: 6:30 daily
- Evening: 19:00 Mon-Sat
- Weekly: 19:00 Sunday

### FAZA 3.2 - Voice App Integration ✅ 2026-01-31

- [x] PAI API extended with project management endpoints
- [x] Voice tools: getProjects, updateProject, addProject, weeklyReview
- [x] On-demand weekly review via voice.stankowski.io
- [x] Natural language deadline parsing in API

**Parallel channels:**
- Telegram: automated check-ins + text commands
- Voice App: on-demand project management + weekly review

### FAZA 3.3 - Mobile Terminal Access ✅ 2026-01-31

- [x] ttyd web terminal on Hetzner
- [x] Caddy reverse proxy with basic auth
- [x] Claude Code accessible via mobile browser
- [x] OAuth credentials for pawel user
- [x] Print mode dla mobile (`claude -p "pytanie"`)
- [x] Interaktywny UI działa na telefonie

**URL:** https://term.stankowski.io
**Auth:** pawel / Voicer5757
**User:** pawel (nie root - bezpieczeństwo)

**Files on server:**
- `/usr/local/bin/ttyd-shell` - Shell wrapper
- `/etc/default/ttyd` - ttyd options
- `/home/pawel/.claude/` - Claude config
- `/home/pawel/p` - Quick print mode script

**Użycie na telefonie:**
```bash
# Interaktywny (pełne UI)
claude

# Szybkie pytanie (print mode)
./p twoje pytanie tutaj

# Kontynuacja rozmowy
claude -c
```

**Re-autoryzacja (gdy token wygaśnie):**
```bash
# Z lokalnego terminala WSL:
ssh -t hetzner "su - pawel -c 'claude auth login'"
```

### FAZA 3.4 - Book Search v1 ✅ 2026-01-31

- [x] Book search automation via Telegram
- [x] Trigger patterns: "szukaj książkę:", "cena książki:", "ile kosztuje:"
- [x] Google Books API integration (price lookup)
- [x] Amazon.pl scraper (ebook prices)

### FAZA 3.5 - Link Fetcher + Book Search v2 ✅ 2026-02-01

#### Link Fetcher (Playwright)
- [x] Playwright + playwright-stealth installed
- [x] X/Twitter fetcher with saved session
- [x] Reddit fetcher with saved session
- [x] Generic page fetcher
- [x] Notion Link Enricher - cron daily 18:00 PL

**New files:**
- `/opt/inbox-webhook/link_fetcher/` - Link fetching module
  - `handler.py` - URL detection + dispatch
  - `x_fetcher.py` - X/Twitter with auth
  - `reddit_fetcher.py` - Reddit with auth
- `/opt/inbox-webhook/notion_link_enricher.py` - Daily enrichment
- `/opt/inbox-webhook/sessions/` - Saved browser sessions
  - `x_cookies.json` - X session
  - `reddit_cookies.json` - Reddit session

**Cron:** `/etc/cron.d/notion-link-enricher` - 17:00 UTC (18:00 PL)

#### Book Search v2 (Playwright)
- [x] Everand searcher (subscription ~45zł/mies)
- [x] Storytel searcher (subscription ~40zł/mies)
- [x] Audible searcher (Playwright, 1 credit)
- [x] Google Play searcher (Playwright)
- [x] Amazon searcher (existing)
- [x] Async wrapper for Playwright
- [x] Grouped output (Subscriptions vs Purchase)

**Updated files:**
- `/opt/inbox-webhook/book_search/searchers/everand.py`
- `/opt/inbox-webhook/book_search/searchers/storytel.py`
- `/opt/inbox-webhook/book_search/searchers/audible.py`
- `/opt/inbox-webhook/book_search/searchers/google_play.py`
- `/opt/inbox-webhook/book_search/playwright_wrapper.py`
- `/opt/inbox-webhook/book_search/handler.py`
- `/opt/inbox-webhook/book_search/formatter.py`

**Credentials in `.env`:**
- `EVERAND_EMAIL`, `EVERAND_PASSWORD`
- `STORYTEL_EMAIL`, `STORYTEL_PASSWORD`
- `REDDIT_USERNAME`, `REDDIT_PASSWORD`
- `X_USERNAME`, `X_PASSWORD`

**Book Search output:**
```
📚 "Atomic Habits" - James Clear

📖 SUBSKRYPCJE:
├─ Everand: audiobook + ebook (w subskrypcji ~45zł/mies)
└─ Storytel: audiobook + ebook (w subskrypcji ~40zł/mies)

💰 KUPNO:
├─ Audible: audiobook (1 credit)
└─ Amazon: ebook 53zł

💡 Najtańsza opcja: Amazon ebook 53zł
```

**Telegram triggers:**
- `szukaj książkę: [tytuł]`
- `@pai szukaj książkę: [tytuł]`

### FAZA 3.6 - Memory Architecture Improvements ✅ 2026-02-01

Based on "Memory in AI Agents" article - implementing production-grade memory patterns.

- [x] **Supersedes field** in Note List (Notion)
  - Self-relation for conflict resolution
  - Links to note this entry replaces/updates
  - Enables "evolve summaries" pattern
- [x] **Last Edited** field in Note List (auto-timestamp)
- [x] **Time decay in context loading**
  - Projects sorted by `Last Review` ascending (oldest first = needs attention)
  - Modified: `/root/.pai/scripts/planner/checkin.py`

**Usage:**
- When creating a note that updates previous info, link via "Supersedes"
- Projects not reviewed recently appear first in check-ins
- Stale projects (>7 days) flagged in weekly review

**Files changed:**
- Notion Note List: +Supersedes (relation), +Last Edited (auto)
- `/root/.pai/scripts/planner/checkin.py`: sorts by Last Review first

### FAZA 4.1 - Overnight Research Briefs ✅ 2026-02-01

System do nocnego researchu: użytkownik wieczorem zleca temat przez Telegram, rano dostaje PDF z opracowaniem.

```
WIECZÓR                        NOC (2:00 AM)                    RANO (6:00)
"@pai zbadaj X"        →    research_worker.py           →    PDF na Telegram
"@pai zbadaj X opus"        ├─ Notion search                    + powiadomienie
                            ├─ Web search (opcja)
                            ├─ DeepSeek/Opus analysis
                            └─ Markdown → PDF
```

**Trigger patterns:**
- `@pai zbadaj: [temat]` → DeepSeek (~$0.03)
- `@pai zbadaj opus: [temat]` → Claude Opus (~$1-2)
- `@pai przeanalizuj: [temat]`
- `@pai research: [temat]`
- `@pai brief: [temat]`
- `@pai zgłęb: [temat]`

**New files on server:**
- `/opt/inbox-webhook/research_handler.py` - Queue management, intent detection
- `/opt/inbox-webhook/research_worker.py` - Overnight processing (Notion + web + AI)
- `/opt/inbox-webhook/research_delivery.py` - Morning PDF delivery
- `/opt/inbox-webhook/web_search.py` - Pluggable web search (Perplexity/Tavily)
- `/opt/inbox-webhook/research_queue/` - Queue directories (pending/processing/done)
- `/opt/inbox-webhook/research_briefs/` - Generated PDF/MD briefs
- `/etc/cron.d/pai-research` - Cron jobs (2:00 AM processing, 6:00 AM delivery)

**Cron schedule:**
- Processing: 2:00 AM CET (1:00 UTC)
- Delivery: 6:00 AM CET (5:00 UTC)

**Dependencies installed:**
- `python-slugify` - Topic slug generation
- `markdown`, `weasyprint` - PDF generation
- `pandoc` - Alternative PDF engine

**Environment variables (optional, in .env):**
```bash
# Web search provider (default: perplexity, fallback: tavily)
WEB_SEARCH_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-xxx

# Alternative after June 2026:
# WEB_SEARCH_PROVIDER=tavily
# TAVILY_API_KEY=tvly-xxx
```

**Cost estimates:**
| Model | Cost/Brief | Use Case |
|-------|------------|----------|
| DeepSeek | $0.02-0.05 | Daily topics, quick research |
| Claude Opus | $1.00-2.00 | Important decisions, deep analysis |

**Test commands:**
```bash
# Test research worker
ssh hetzner "cd /opt/inbox-webhook && /opt/inbox-webhook/venv/bin/python research_worker.py --test"

# Test delivery
ssh hetzner "cd /opt/inbox-webhook && /opt/inbox-webhook/venv/bin/python research_delivery.py --test"

# Check queue
ssh hetzner "ls /opt/inbox-webhook/research_queue/*/"

# Check briefs
ssh hetzner "ls /opt/inbox-webhook/research_briefs/"
```

### FAZA 4.2 - Voice App Notion Integration ✅ 2026-02-01

Rozszerzenie voice.stankowski.io o dostęp do Note List i Books Tracker z Notion.

**New API endpoints (pai_api.py):**
- `GET /api/note-list` - List notes with filters (type, status, area)
- `GET /api/note-list/search?q=` - Search notes
- `GET /api/books` - List books with filters (status, author)
- `GET /api/books/search?q=` - Search books
- `GET /api/books/reading` - Currently reading
- `GET /api/books/to-read` - Reading list

**New voice tools (liveClient.ts):**
- `searchNotes` - "znajdź w notatkach..."
- `searchBooks` - "znajdź książkę..."
- `getCurrentlyReading` - "co czytam?"
- `getReadingList` - "co mam do przeczytania?"

**Database IDs:**
- Note List: `cb912123-bf69-4623-b08c-43fd8e03d9cd`
- Books Tracker: `20cd6ad6-369a-803a-a25d-f2bfd4683d36`

**Voice commands:**
```
"Co czytam?" → Lista książek (Reading)
"Szukaj w notatkach AI" → Wyszukuje w Note List
"Znajdź książki Vonneguta" → Szuka po autorze
"Jaka jest moja lista do przeczytania?" → Books To Read
```

**Files changed:**
- `/opt/inbox-webhook/pai_api.py` - Added endpoints + helper functions
- `/mnt/e/voice/nexus-voice-interface/services/liveClient.ts` - Added tools
- `/var/www/pai-voice/` - Deployed updated voice app

### FAZA 4.3 - Observatory Dashboard ✅ 2026-02-07

Real-time observability dashboard integrated into voice.stankowski.io.

**Features:**
- System status (services health, queue depth)
- Telegram inbox events (voice/photo/text with transcriptions)
- Voice app session transcripts (expandable conversations)
- Link enrichment history (X/Reddit extractions)
- Research brief pipeline (queue → processing → delivered)
- Tab navigation: All | Inbox | Voice | Links | Research
- Auto-refresh every 30 seconds

**New API endpoints (pai_api.py v2.1.0):**
- `GET /api/observatory/status` - Service health + queue stats
- `GET /api/observatory/events` - Recent inbox events
- `GET /api/observatory/voice-sessions` - Voice app transcripts
- `GET /api/observatory/link-enrichment` - Link extraction history
- `GET /api/observatory/research` - Research brief pipeline
- `GET /api/observatory/metrics` - Aggregate stats
- `GET /api/observatory/errors` - Recent failures
- `GET /api/observatory/stream` - SSE for real-time updates

**Frontend (voice.stankowski.io):**
- New Observatory view (📊 icon in header)
- Tab-based navigation between data sources
- Expandable voice session transcripts
- Status indicators for services
- Event cards with AI response previews

**Files created/modified:**
- `/opt/inbox-webhook/pai_api.py` - Added observatory endpoints (v2.1.0)
- `/mnt/e/voice/nexus-voice-interface/components/Observatory.tsx` - New component
- `/mnt/e/voice/nexus-voice-interface/types.ts` - Observatory types
- `/mnt/e/voice/nexus-voice-interface/App.tsx` - Observatory navigation

**Access:** https://voice.stankowski.io → click 📊 icon

### FAZA 4.4 - Link Enricher Type/Tags Auto-Detection ✅ 2026-02-08

Extended `notion_link_enricher.py` to auto-classify link entries with Type and Tags using DeepSeek.

- [x] `classify_content()` - DeepSeek API classifies content into Type + Tags
- [x] `update_note()` - Extended to write Type (rich_text) and Tags (multi_select)
- [x] Wired into `enrich_links()` main loop
- [x] `--dry-run` CLI flag for safe testing
- [x] Fallback: defaults to `Article` + empty tags on failure

**Type values:** Article, Tool, Video, Book, Podcast, Thread, Discussion, Note
**Tags:** 2-5 short English labels auto-generated from content

**Cost:** ~$0.005/entry (DeepSeek deepseek-chat)

**Files changed:**
- `/opt/inbox-webhook/notion_link_enricher.py` - Added `classify_content()`, renamed `update_note_content()` → `update_note()`, added `import openai`

**Test:**
```bash
ssh hetzner "cd /opt/inbox-webhook && /opt/inbox-webhook/venv/bin/python notion_link_enricher.py --dry-run"
```

### FAZA 4.5 - Voice App Inbox Access ✅ 2026-02-14

Added inbox message querying to the voice app. Previously, asking "do I have messages?" returned nothing because there was no tool or API endpoint for inbox access.

- [x] `GET /api/inbox` endpoint in PAI API (sorted by timestamp, supports limit & type_filter)
- [x] `getInboxMessages` voice tool in liveClient.ts
- [x] Returns voice transcriptions, photo descriptions, text messages
- [x] Includes AI responses if any were triggered

**New API endpoint (pai_api.py):**
- `GET /api/inbox?limit=10&type_filter=voice` - List inbox messages (newest first)

**New voice tool (liveClient.ts):**
- `getInboxMessages` - "check my inbox", "any new messages?", "co mam w inboxie?"

**Files changed:**
- `/opt/inbox-webhook/pai_api.py` - Added `/api/inbox` endpoint
- `/mnt/e/voice/nexus-voice-interface/services/liveClient.ts` - Added `getInboxMessages` tool + handler

**Voice commands:**
```
"Do I have any messages?" → Lists recent inbox messages
"Check my inbox" → Same
"Co mam w inboxie?" → Same (Polish)
"Show me voice messages" → Filtered by type=voice
```

### FAZA 4 - Future

**From claude.ai conversation (Jan 2026) - NOT yet implemented:**
- [ ] GTD Stage property in Note List (Inbox, Next Actions, Projects, Waiting For, Someday/Maybe, Reference)
- [ ] Smart Notion Views (Process Inbox, This Week, High Value)
- [ ] Knowledge Graph / Related Notes (relation field between notes)
- [ ] Score auto-detection (AI priority 1-5)
- [ ] Area auto-detection (Work/Private - Type & Tags done, Area missing)
- [ ] Daily Brief generator (morning summary)
- [ ] Topic clustering (group notes by themes)
- [ ] Bulk Import session mode ("5 ideas at once → 5 entries")

**Other future ideas:**
- [ ] Voice check-in (extend pai-voice-app)
- [ ] Voice responses (TTS) - send voice messages back
- [ ] Smart reminders (deadline approaching)
- [ ] Semantic search
- [ ] Pattern detection in habits
- [ ] Web dashboard
- [ ] Book search: Price alerts ("powiadom gdy < 30zł")
- [ ] Book search: Price caching (24h)
- [ ] Research: Recurring research (weekly updates on topic)
- [ ] Research: Voice summary option (TTS before PDF)

---

## Test Commands

### Test webhook

```bash
curl -X POST https://api.stankowski.io/hook/n8n \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: $(ssh hetzner 'grep WEBHOOK_SECRET /opt/inbox-webhook/.env | cut -d= -f2')" \
  -d '{
    "event_id": "test_'$(date +%s)'",
    "type": "text",
    "drive_path": "/inbox/test.txt",
    "timestamp": "'$(date -Iseconds)'"
  }'
```

### Check health

```bash
curl https://api.stankowski.io/health
```

---

## SSH Configuration

SSH alias `hetzner` configured in `~/.ssh/config`:
```
Host hetzner
    HostName 157.180.26.47
    User root
    IdentityFile ~/.ssh/id_ed25519
```

---

## Related Files

- `/home/pawel/.pai/inbox/README.md` - Full documentation
- `/home/pawel/.claude/skills/InboxProcessor/SKILL.md` - Processing skill
- `/home/pawel/.pai/sync-inbox.sh` - Sync script

---

## Notes

- Webhook secret is stored in /opt/inbox-webhook/.env on server
- Events from Telegram are test data (Aaa, Bbb, Uuu, Hhhhh)
- n8n integration not yet configured (manual webhook tests only)
- Worker processes events but doesn't download files yet (needs GDrive creds)
