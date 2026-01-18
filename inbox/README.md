# PAI Inbox System - FAZA 1 MVP

Voice-first, mobile-first personal knowledge capture system.

## 📱 How It Works

```
1. You send → Telegram (voice/photo/text)
2. n8n collects → Google Drive
3. n8n triggers → https://api.stankowski.io/hook/n8n
4. Worker processes → /opt/inbox-webhook/downloads/
5. You sync → ~/.pai/inbox/raw/
6. Claude processes → ~/.pai/memory/
```

## 🏗️ Architecture

### Server Side (Hetzner)

**Location:** `/opt/inbox-webhook/`

**Components:**
- `main.py` - FastAPI webhook receiver (port 8010)
- `worker.py` - Queue processor (polling every 2s)
- `process_event.py` - Event handler (MVP - metadata only)

**Services:**
- `inbox-webhook.service` - Webhook API
- `inbox-worker.service` - Background processor

**Directories:**
```
/opt/inbox-webhook/
├── queue/          # Incoming events
├── processing/     # Currently being processed
├── done/           # Processed successfully
├── failed/         # Processing errors
├── downloads/      # Event data + metadata
│   └── <event_id>/
│       └── metadata.json
└── logs/           # Application logs
```

**Endpoints:**
- `POST https://api.stankowski.io/hook/n8n` - Receive events from n8n
  - Header: `X-Webhook-Secret: <secret>`
  - Body: InboxEvent JSON

### Local Side (WSL/PAI)

**Location:** `~/.pai/inbox/`

**Directories:**
```
~/.pai/inbox/
├── raw/            # Synced from server
├── processed/      # After Claude processing
└── archive/        # Old events (>30 days)
```

**Tools:**
- `~/.pai/sync-inbox.sh` - Sync events from server
- `~/.claude/skills/InboxProcessor/` - Claude skill for processing

## 🚀 Quick Start

### 1. Send test event to webhook

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

### 2. Sync events from server

```bash
~/.pai/sync-inbox.sh
```

### 3. Process with Claude

```bash
claude
# Then: /InboxProcessor
```

## 📊 Monitoring

### Check server status

```bash
# Service status
ssh hetzner "systemctl status inbox-webhook inbox-worker"

# Recent logs
ssh hetzner "journalctl -u inbox-worker -n 20 --no-pager"

# Queue stats
ssh hetzner "ls /opt/inbox-webhook/{queue,done,failed}/*.json 2>/dev/null | wc -l"
```

### Check local status

```bash
# Count raw events
ls -1 ~/.pai/inbox/raw/ | wc -l

# Count processed
ls -1 ~/.pai/inbox/processed/ | wc -l

# Recent events
ls -lt ~/.pai/inbox/raw/ | head
```

## 🔐 Security

**Webhook Secret:**
```bash
ssh hetzner "cat /opt/inbox-webhook/.env | grep WEBHOOK_SECRET"
```

**Update secret:**
```bash
ssh hetzner "nano /opt/inbox-webhook/.env"
ssh hetzner "systemctl restart inbox-webhook"
```

## 📝 n8n Integration

**Webhook URL:** `https://api.stankowski.io/hook/n8n`

**Headers:**
```
X-Webhook-Secret: <your-secret>
Content-Type: application/json
```

**Payload:**
```json
{
  "event_id": "{{$execution.id}}-{{$now}}",
  "type": "voice",
  "drive_file_id": "{{$json.fileId}}",
  "drive_path": "TelegramInbox/2026-01-17/voice_123.ogg",
  "timestamp": "{{$now}}",
  "metadata": {
    "duration_sec": 45,
    "from": "telegram"
  }
}
```

## 🔄 Event Types

| Type | Description | MVP Status |
|------|-------------|------------|
| `text` | Text message | ✅ Metadata only |
| `voice` | Voice note | ✅ Metadata only |
| `photo` | Image | ✅ Metadata only |
| `document` | File attachment | ✅ Metadata only |

## 🎯 FAZA 1 Status

**✅ Implemented:**
- [x] Webhook endpoint with auth
- [x] File-based queue system
- [x] Worker with polling
- [x] Event processing (metadata)
- [x] Systemd services (auto-restart)
- [x] HTTPS + Caddy reverse proxy
- [x] Idempotency check
- [x] Structured logging
- [x] Local PAI integration
- [x] Sync script
- [x] InboxProcessor skill scaffold

**⏳ TODO (FAZA 2):**
- [ ] Google Drive API integration (download files)
- [ ] Audio transcription (Whisper)
- [ ] Image OCR/description (Claude Vision)
- [ ] Auto-sync (inotify/watchdog)
- [ ] Claude Code auto-processing
- [ ] Notification system

**🚀 TODO (FAZA 3):**
- [ ] Semantic search
- [ ] Topic clustering
- [ ] Proactive insights
- [ ] Web dashboard

## 🛠️ Troubleshooting

### Webhook not receiving events

```bash
# Check service
ssh hetzner "systemctl status inbox-webhook"

# Test locally
ssh hetzner "curl -s http://127.0.0.1:8010/health"

# Check Caddy config
ssh hetzner "cat /etc/caddy/Caddyfile | grep -A 5 'api.stankowski.io'"
```

### Worker not processing

```bash
# Check service
ssh hetzner "systemctl status inbox-worker"

# Check logs
ssh hetzner "tail -f /opt/inbox-webhook/logs/worker.log"

# Manual test
ssh hetzner "cd /opt/inbox-webhook && source venv/bin/activate && python3 worker.py"
```

### Events stuck in queue

```bash
# Check queue
ssh hetzner "ls -la /opt/inbox-webhook/queue/"

# Check failed
ssh hetzner "ls -la /opt/inbox-webhook/failed/"
ssh hetzner "cat /opt/inbox-webhook/failed/*.error.txt"

# Restart worker
ssh hetzner "systemctl restart inbox-worker"
```

## 📚 Files Reference

### Server

- `/opt/inbox-webhook/main.py` - Webhook API (FastAPI)
- `/opt/inbox-webhook/worker.py` - Queue processor
- `/opt/inbox-webhook/process_event.py` - Event handler
- `/opt/inbox-webhook/.env` - Config (WEBHOOK_SECRET)
- `/etc/systemd/system/inbox-webhook.service` - Webhook service
- `/etc/systemd/system/inbox-worker.service` - Worker service
- `/etc/caddy/Caddyfile` - Reverse proxy config

### Local

- `~/.pai/inbox/` - Event storage
- `~/.pai/sync-inbox.sh` - Sync script
- `~/.claude/skills/InboxProcessor/SKILL.md` - Processing skill
- `~/.pai/memory/short-term/` - Processed notes (future)

---

**Created:** 2026-01-17
**Status:** FAZA 1 MVP Complete ✅
**Next:** Add Google Drive integration for file downloads
