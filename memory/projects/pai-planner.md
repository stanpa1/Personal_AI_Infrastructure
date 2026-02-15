# PAI Planner - Project Tracking System

**Status:** active
**Created:** 2026-01-30
**Last Updated:** 2026-01-31
**Priority:** high

---

## System Overview

PAI Planner to proaktywny system zarządzania projektami z automatycznymi check-inami. Działa 24/7 na serwerze Hetzner, wysyłając przypomnienia przez Telegram o 6:30 i 19:00.

### Kluczowe funkcje

- **Daily Check-ins** - automatyczne podsumowania rano i wieczorem
- **Notion Integration** - projekty przechowywane w Notion, pobierane przez API
- **DeepSeek AI** - generowanie naturalnych wiadomości check-in
- **Multi-modal** - Telegram (działa), Voice (planowane), CLI (działa)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       HETZNER (24/7)                            │
│                       IP: [server]                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    /root/.pai/                          │   │
│  │  ├── memory/projects/     # Dokumentacja projektów      │   │
│  │  ├── telos/               # Misja, wartości             │   │
│  │  ├── scripts/planner/     # Check-in scripts            │   │
│  │  │   └── checkin.py       # Main check-in logic         │   │
│  │  └── logs/                # Logi check-inów             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              /opt/inbox-webhook/                         │   │
│  │  ├── main.py              # Webhook API                 │   │
│  │  ├── worker.py            # Event processor             │   │
│  │  ├── telegram_sender.py   # Telegram integration        │   │
│  │  ├── claude_handler.py    # DeepSeek AI handler         │   │
│  │  ├── venv/                # Python virtual environment  │   │
│  │  └── .env                 # API keys                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┼──────────────────────────────┐  │
│  │                     CRON JOBS                            │  │
│  │  5:30 UTC (6:30 PL)  → morning check-in                 │  │
│  │  18:00 UTC (19:00 PL) → evening check-in                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
    ┌─────────┐         ┌──────────┐        ┌───────────┐
    │ Notion  │         │ DeepSeek │        │ Telegram  │
    │   API   │         │   API    │        │   Bot     │
    └─────────┘         └──────────┘        └───────────┘
```

---

## Configuration Details

### Notion Database

- **Database ID:** `f357240c-2d5b-4694-87f8-2f10a174a46e`
- **URL:** https://www.notion.so/f357240c2d5b469487f82f10a174a46e
- **Integration:** Connected to "MCP Integration" and "Notn8n"

#### Schema

| Property | Type | Description |
|----------|------|-------------|
| Name | title | Nazwa projektu |
| Area | select | 💼 Praca / 🏠 Dom / 💪 Zdrowie / 📚 Rozwój / 💰 Finanse |
| Status | select | 🔵 Active / ⏸️ Paused / ⏳ Waiting / 💤 Someday / ✅ Done |
| Priority | select | 🔴 High / 🟡 Medium / 🟢 Low |
| Next Action | text | Konkretny następny krok |
| Action Deadline | date | Deadline na next action |
| Waiting For | text | Na co/kogo czekasz |
| Risk | text | Znane ryzyka lub blokery |
| Last Review | date | Ostatni check-in (auto-update) |
| Notes | text | Kontekst, historia |

### Telegram

- **Chat ID:** `-1003590663382`
- **Bot:** Używa TELEGRAM_BOT_TOKEN z .env
- **Trigger:** `@pai` dla interaktywnych zapytań

### API Keys (w /opt/inbox-webhook/.env)

- `NOTION_API_TOKEN` - Notion Integration token
- `DEEPSEEK_API_KEY` - DeepSeek chat API
- `TELEGRAM_BOT_TOKEN` - Telegram Bot
- `OPENAI_API_KEY` - Whisper transcription
- `ANTHROPIC_API_KEY` - Claude (backup)

### Cron Configuration

File: `/etc/cron.d/pai-checkin`

```cron
# Morning check-in at 6:30 Warsaw time (5:30 UTC)
30 5 * * * root cd /root/.pai && /opt/inbox-webhook/venv/bin/python /root/.pai/scripts/planner/checkin.py morning >> /root/.pai/logs/checkin.log 2>&1

# Evening check-in at 19:00 Warsaw time (18:00 UTC)
0 18 * * * root cd /root/.pai && /opt/inbox-webhook/venv/bin/python /root/.pai/scripts/planner/checkin.py evening >> /root/.pai/logs/checkin.log 2>&1
```

---

## Check-in Flow

### Morning (6:30)

1. Cron triggers `checkin.py morning`
2. Fetch Active projects from Notion API
3. Filter High priority + upcoming deadlines
4. DeepSeek generates personalized message
5. Send to Telegram
6. Log result

### Evening (19:00)

1. Cron triggers `checkin.py evening`
2. Fetch Active projects from Notion API
3. Focus on High priority progress
4. DeepSeek generates summary/questions
5. Send to Telegram
6. Log result

### User Response Flow

1. User responds in Telegram
2. inbox-webhook receives via n8n
3. If starts with `@pai` → claude_handler processes
4. Response sent back to Telegram

---

## Files on Server

### /root/.pai/scripts/planner/checkin.py

Main check-in script:
- `get_notion_projects()` - Fetch from Notion API
- `generate_checkin_with_deepseek()` - AI message generation
- `generate_fallback_message()` - Backup if AI fails
- `send_checkin_message()` - Telegram delivery

### /root/.pai/logs/checkin.log

Check-in execution logs with timestamps.

---

## Current Status (2026-01-31)

### Working ✅

- [x] PAI migrated to Hetzner
- [x] Notion API integration
- [x] DeepSeek message generation
- [x] Telegram delivery
- [x] Morning/Evening cron jobs
- [x] 5 test projects in database

### Pending 🔄

- [ ] Update Last Review automatically after check-in
- [ ] Parse user responses to update projects
- [ ] Weekly review (Sunday 19:00)
- [ ] Voice check-in integration

---

## Next Development Phases

### Phase 3.1: Response Processing (Priority: High)

Enable PAI to understand and act on check-in responses.

**Tasks:**
- [ ] Detect project status updates in responses ("Matryce - done")
- [ ] Update Notion projects via API
- [ ] Confirm changes back to user
- [ ] Handle "add new project" requests

**Example flow:**
```
PAI: "Jak poszło z Matryce międzynarodowe?"
User: "skończone, przeczytałem koncepcję Nika"
PAI: → Updates Notion: Next Action = "Spotkanie z Nikiem", Last Review = today
PAI: "Zapisałem! Spotkanie we wtorek - potrzebujesz się przygotować?"
```

### Phase 3.2: Weekly Review (Priority: Medium)

**Tasks:**
- [ ] Add Sunday 19:00 cron job
- [ ] Generate weekly summary (completed, in progress, stale)
- [ ] Pattern detection ("odkładasz admin tasks")
- [ ] Planning prompts for next week

### Phase 3.3: Voice Check-in (Priority: Medium)

Extend pai-voice-app for check-in mode.

**Tasks:**
- [ ] Add "check-in" voice command
- [ ] TTS responses via ElevenLabs
- [ ] Same logic as Telegram, different interface
- [ ] Useful when driving/hands busy

### Phase 3.4: Smart Reminders (Priority: Low)

Proactive nudges beyond scheduled check-ins.

**Tasks:**
- [ ] Deadline approaching (24h, 4h before)
- [ ] Stale project (no update >5 days)
- [ ] Blocked project needs attention
- [ ] High priority not started

### Phase 3.5: Browser Integration (Priority: Low)

Add Playwright MCP for web automation.

**Tasks:**
- [ ] Install Playwright on Hetzner
- [ ] Auto-fetch article content from links
- [ ] Price monitoring alerts
- [ ] Calendar integration (read events)

---

## Commands Reference

### SSH Access
```bash
ssh hetzner
cd ~/.pai
```

### Manual Check-in
```bash
ssh hetzner '/opt/inbox-webhook/venv/bin/python ~/.pai/scripts/planner/checkin.py morning'
ssh hetzner '/opt/inbox-webhook/venv/bin/python ~/.pai/scripts/planner/checkin.py evening'
```

### View Logs
```bash
ssh hetzner 'tail -50 ~/.pai/logs/checkin.log'
```

### Service Status
```bash
ssh hetzner 'systemctl status inbox-webhook inbox-worker'
```

### Test Notion Connection
```bash
ssh hetzner 'source /opt/inbox-webhook/.env && curl -s -X POST "https://api.notion.com/v1/databases/f357240c-2d5b-4694-87f8-2f10a174a46e/query" -H "Authorization: Bearer $NOTION_API_TOKEN" -H "Notion-Version: 2022-06-28" | python3 -m json.tool | head -50'
```

---

## Sync Configuration

### Local → Hetzner
```bash
rsync -avz ~/.pai/ hetzner:~/.pai/
rsync -avz ~/.claude/ hetzner:~/.claude/
```

### Working with PAI remotely
```bash
ssh -t hetzner "cd ~/.pai && claude"
```

---

## Notes

- Serwer timezone: UTC (cron times adjusted for Warsaw = UTC+1)
- DeepSeek jest znacznie tańszy niż Claude API
- Fallback message generowany jeśli AI zawiedzie
- Projekty ~30 (10-20 praca + 10 prywatne)
- User prefers assertive reminders ("natrętność OK")
