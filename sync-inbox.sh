#!/bin/bash
# Sync inbox events from Hetzner server to local PAI

set -e

REMOTE="hetzner:/opt/inbox-webhook/downloads/"
LOCAL="$HOME/.pai/inbox/raw/"

echo "📥 Syncing inbox events from server..."
echo "Remote: $REMOTE"
echo "Local: $LOCAL"
echo ""

# Sync downloads directory
rsync -avz --progress "$REMOTE" "$LOCAL"

echo ""
echo "✅ Sync complete!"
echo ""

# Count events
EVENT_COUNT=$(find "$LOCAL" -mindepth 1 -maxdepth 1 -type d | wc -l)
echo "📊 Total events in raw/: $EVENT_COUNT"

# Show recent events
echo ""
echo "📋 Recent events:"
find "$LOCAL" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort -r | head -5

echo ""
echo "💡 Next step: Run Claude Code to process these events"
echo "   Command: claude"
echo "   Then say: /InboxProcessor"
