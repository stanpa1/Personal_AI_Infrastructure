#!/bin/bash
# Weekly Digest Generator for PAI + Notion
# Runs every Sunday at 20:00 via cron
#
# Cron entry: 0 20 * * 0 /home/pawel/.pai/scripts/notion/generate-digest.sh

LOG_FILE="/home/pawel/.pai/logs/notion-digest.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

mkdir -p /home/pawel/.pai/logs

echo "[$TIMESTAMP] Weekly Digest triggered" >> "$LOG_FILE"

# Option 1: Send reminder via PAI voice server (if running)
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3456/health 2>/dev/null | grep -q "200"; then
    curl -s -X POST http://localhost:3456/notify \
        -H "Content-Type: application/json" \
        -d '{"message": "Czas na weekly digest. Powiedz: wygeneruj podsumowanie tygodnia."}' \
        >> "$LOG_FILE" 2>&1
    echo "[$TIMESTAMP] Voice notification sent" >> "$LOG_FILE"
fi

# Option 2: Send Telegram reminder via PAI inbox system (if configured)
if [ -f "/home/pawel/.pai/.env" ]; then
    source /home/pawel/.pai/.env
    if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=📊 Przypomnienie: Czas na weekly digest! Powiedz @pai wygeneruj podsumowanie tygodnia" \
            >> "$LOG_FILE" 2>&1
        echo "[$TIMESTAMP] Telegram reminder sent" >> "$LOG_FILE"
    fi
fi

# Option 3: Create a reminder file in inbox
REMINDER_FILE="/home/pawel/.pai/inbox/raw/weekly-digest-reminder-$(date +%Y%m%d).json"
cat > "$REMINDER_FILE" << EOF
{
    "event_id": "digest_reminder_$(date +%s)",
    "type": "reminder",
    "timestamp": "$TIMESTAMP",
    "message": "Weekly Digest - uruchom NotionDigest skill",
    "action": "generate_weekly_digest"
}
EOF

echo "[$TIMESTAMP] Reminder file created: $REMINDER_FILE" >> "$LOG_FILE"
echo "[$TIMESTAMP] Weekly Digest reminder complete" >> "$LOG_FILE"
