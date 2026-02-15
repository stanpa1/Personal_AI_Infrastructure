#!/bin/bash
# Sync PAI context to Hetzner server
# Runs every 2 hours during daytime (8:00-22:00)
# Crontab: 0 8-22/2 * * * ~/.pai/sync-pai-context.sh

LOGFILE=~/.pai/logs/sync-context.log
mkdir -p ~/.pai/logs

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting PAI context sync..." >> "$LOGFILE"

rsync -av --delete \
    ~/.pai/memory/ \
    ~/.pai/telos/ \
    hetzner:/opt/inbox-webhook/pai-context/ \
    >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync completed successfully" >> "$LOGFILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Sync FAILED" >> "$LOGFILE"
fi
