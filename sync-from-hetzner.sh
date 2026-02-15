#!/bin/bash
# Sync PAI context FROM Hetzner to local PC
# Run at session start to get latest changes made via mobile

REMOTE="hetzner:/opt/inbox-webhook/pai-context"
LOCAL="$HOME/.pai"

echo "📥 Syncing PAI context from Hetzner..."

# Sync memory (projects, notes)
rsync -avz --update "$REMOTE/memory/" "$LOCAL/memory/" 2>/dev/null

# Sync telos if exists
rsync -avz --update "$REMOTE/telos/" "$LOCAL/telos/" 2>/dev/null

echo "✅ Sync from Hetzner complete"
