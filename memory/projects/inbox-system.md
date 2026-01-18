# Inbox System - Project Status

**Last Updated:** 2026-01-18
**Status:** FAZA 1 MVP Complete, FAZA 2 In Progress

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

### FAZA 3 - Future

- [ ] Semantic search
- [ ] Topic clustering
- [ ] Proactive insights
- [ ] Web dashboard
- [ ] Telegram callback notifications

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
