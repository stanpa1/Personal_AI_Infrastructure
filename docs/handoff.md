# PAI Telegram Bidirectional Communication - Session Handoff

**Date:** 2026-01-18
**Session Goal:** Implement bidirectional Telegram ↔ AI communication for PAI

---

## What Was Implemented

### 1. Bidirectional Telegram Communication
Users can now send `@pai <question>` via Telegram and receive AI-powered responses.

```
Flow:
Telegram → n8n → GDrive → Hetzner webhook → worker → DeepSeek API → Telegram Bot → User
```

### 2. New Server Components

| File | Purpose |
|------|---------|
| `/opt/inbox-webhook/telegram_sender.py` | Sends responses back to Telegram |
| `/opt/inbox-webhook/claude_handler.py` | Processes queries via DeepSeek with PAI context |
| `/opt/inbox-webhook/process_event.py` | Updated with Claude handler integration |
| `/opt/inbox-webhook/worker.py` | Timeout increased to 600s |

### 3. PAI Context Sync
Local PAI memory is synced to server for context-aware responses.

```
Local: ~/.pai/memory/, ~/.pai/telos/
  ↓ rsync (cron: every 2h, 8:00-22:00)
Server: /opt/inbox-webhook/pai-context/
```

**Cron job:** `0 8-22/2 * * * ~/.pai/sync-pai-context.sh`

### 4. AI Model: DeepSeek
Switched from GPT-5.2 to DeepSeek for cost efficiency (~10-40x cheaper).

---

## Configuration

### Server .env (`/opt/inbox-webhook/.env`)
```bash
WEBHOOK_SECRET=9P9gkqxaGCCJDNiEcCtj09sjB7nDVMLSt_QXPbF2GMg
GDRIVE_CREDENTIALS_PATH=/opt/inbox-webhook/credentials.json
OPENAI_API_KEY=sk-proj-...      # For Whisper/Vision
ANTHROPIC_API_KEY=sk-ant-...    # Not used (no credits)
TELEGRAM_BOT_TOKEN=8587209689:AAHOmh_1OQBAA9-CkmaSx1J8-pHYGZjRIEU
DEEPSEEK_API_KEY=sk-d6b8034a4b65423d87469ee70313695a
CLAUDE_TRIGGER_PREFIX=@pai
CLAUDE_TIMEOUT_SECONDS=120
```

### Telegram Bot
- **Username:** @ytpawelbot
- **Chat ID:** -1003590663382 (group)

---

## Quick Commands

### Check Service Status
```bash
ssh hetzner "systemctl status inbox-webhook inbox-worker --no-pager"
```

### View Worker Logs
```bash
ssh hetzner "journalctl -u inbox-worker -f"
```

### Manual Context Sync
```bash
~/.pai/sync-pai-context.sh
```

### Restart Worker
```bash
ssh hetzner "systemctl restart inbox-worker"
```

### Check Synced Context
```bash
ssh hetzner "ls -la /opt/inbox-webhook/pai-context/"
```

### Test DeepSeek API Directly
```bash
ssh hetzner "/opt/inbox-webhook/venv/bin/python3 -c \"
from dotenv import load_dotenv
from pathlib import Path
import os
load_dotenv(Path('/opt/inbox-webhook/.env'))
import sys
sys.path.insert(0, '/opt/inbox-webhook')
from claude_handler import process_with_claude
success, response = process_with_claude('Jaki projekt aktualnie realizuję?')
print(response)
\""
```

---

## Local Files Created

| File | Purpose |
|------|---------|
| `~/.pai/sync-pai-context.sh` | Rsync script for PAI context |
| `~/.pai/logs/sync-context.log` | Sync log file |
| `~/.pai/inbox/server-files/*.py` | Local copies of server scripts |

---

## What's Loaded as Context

The AI receives this context with every `@pai` query:

1. **Telos** (~800 chars)
   - `mission.md` - user goals and preferences
   - `beliefs.md` - communication style
   - `strategies.md` - problem-solving approach

2. **Projects** (max 5, 2000 chars each)
   - `projects/*.md` - active project status

3. **Recent Notes** (last 10, 500 chars each)
   - `short-term/*.md` - recent voice/text/photo notes

**Total context:** ~5000 chars currently

---

## Next Steps (Future Enhancements)

### Option A: Voice Responses via TTS (Easy)
Add text-to-speech to send voice messages back instead of text.

```python
# In telegram_sender.py - add send_voice_message()
# Use OpenAI TTS: client.audio.speech.create(model="tts-1", voice="alloy", input=text)
# Send as Telegram voice message
```

### Option B: Realtime Voice Web App (Medium)
Create a web interface for real-time voice conversation.

```
Components needed:
1. HTML/JS page with WebSocket to OpenAI Realtime API
2. HTTPS endpoint (e.g., voice.stankowski.io)
3. PAI context injection into Realtime session
```

### Option C: Expand Context Sources
- Add `mid-term/` and `long-term/` memory
- Include calendar/contacts if available
- Implement RAG for larger knowledge bases

---

## Troubleshooting

### "Błąd API" response
- Check API key validity
- Check DeepSeek balance: https://platform.deepseek.com
- View logs: `ssh hetzner "journalctl -u inbox-worker -n 50"`

### No response in Telegram
- Verify bot token is correct
- Check chat_id extraction in logs
- Ensure worker is running

### Context not updating
- Run manual sync: `~/.pai/sync-pai-context.sh`
- Check cron: `crontab -l`
- Verify SSH key access to hetzner

---

## Architecture Diagram

```
┌─────────────┐     ┌─────────┐     ┌─────────────┐
│  Telegram   │────▶│   n8n   │────▶│ Google Drive│
│  (mobile)   │     │         │     │             │
└─────────────┘     └─────────┘     └──────┬──────┘
       ▲                                   │
       │                                   ▼
       │                          ┌────────────────┐
       │                          │ Hetzner Server │
       │                          │                │
       │    ┌─────────────────────┤ inbox-webhook  │
       │    │                     │ (FastAPI)      │
       │    │                     └───────┬────────┘
       │    │                             │
       │    │                     ┌───────▼────────┐
       │    │                     │ inbox-worker   │
       │    │                     │ (queue processor)
       │    │                     └───────┬────────┘
       │    │                             │
       │    │  ┌──────────────────────────┼──────────────────┐
       │    │  │                          ▼                  │
       │    │  │  ┌─────────────┐  ┌─────────────┐          │
       │    │  │  │ Whisper STT │  │ GPT-4 Vision│          │
       │    │  │  │ (audio)     │  │ (images)    │          │
       │    │  │  └─────────────┘  └─────────────┘          │
       │    │  │                          │                  │
       │    │  │                  ┌───────▼────────┐         │
       │    │  │                  │ claude_handler │         │
       │    │  │                  │ (DeepSeek API) │         │
       │    │  │                  └───────┬────────┘         │
       │    │  │                          │                  │
       │    │  │  ┌───────────────────────┘                  │
       │    │  │  │  pai-context/                            │
       │    │  │  │  (synced from local)                     │
       │    │  │  │  - telos/*.md                            │
       │    │  │  │  - projects/*.md                         │
       │    │  │  │  - short-term/*.md                       │
       │    │  └──┼──────────────────────────────────────────┘
       │    │     │
       │    │     ▼
       │    │  ┌─────────────────┐
       └────┼──│ telegram_sender │
            │  │ (Bot API)       │
            │  └─────────────────┘
            │
    ┌───────┴───────┐
    │ Local Machine │
    │ ~/.pai/       │
    │ (rsync 2h)    │
    └───────────────┘
```

---

## Session Statistics

- **Duration:** ~45 minutes
- **Files created:** 5
- **Files modified:** 4
- **Services configured:** 2
- **APIs integrated:** DeepSeek, Telegram Bot, OpenAI (Whisper/Vision)
