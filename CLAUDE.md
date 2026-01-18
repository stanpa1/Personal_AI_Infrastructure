# PAI Repository Context

This is the Personal AI Infrastructure (PAI) repository - a framework for building your own AI assistant.

## Active Projects

When starting a session, check these files for context on ongoing work:

### Inbox System (Priority: Active)
**Status:** FAZA 1 Complete, FAZA 2 In Progress
**File:** `memory/projects/inbox-system.md`

Voice-first mobile capture system: Telegram → n8n → GDrive → Hetzner webhook → PAI memory.

**Quick status check:**
```bash
ssh hetzner "systemctl status inbox-webhook inbox-worker --no-pager"
```

---

## Directory Structure

```
~/.pai/
├── inbox/              # Telegram inbox system
│   ├── raw/            # Synced events from server
│   ├── processed/      # After processing
│   └── archive/        # Old events
├── memory/
│   ├── short-term/     # Recent notes (7 days)
│   ├── mid-term/       # Important (7-30 days)
│   ├── long-term/      # Knowledge base
│   └── projects/       # Active project status
├── telos/              # Beliefs, mission, strategies
├── Packs/              # PAI extension packs
└── sync-inbox.sh       # Sync script for inbox
```

## Key Commands

```bash
# Sync inbox from server
~/.pai/sync-inbox.sh

# SSH to Hetzner server
ssh hetzner

# Check inbox services
ssh hetzner "systemctl status inbox-webhook inbox-worker"
```

## Related Locations

- `~/.claude/skills/` - Claude Code skills (InboxProcessor, etc.)
- `~/.claude/settings.json` - Claude Code configuration
