#!/bin/bash

# Health-check script for MWRD Lake Levels Dashboard.
# Checks if the Flask server is responding on port 5000.
# If not, restarts it via start.sh.
# Intended to be run every 10 minutes via cron.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/server.pid"
LOG_FILE="$SCRIPT_DIR/healthcheck.log"
LOCK_FILE="/tmp/lake-levels-healthcheck.lock"

# Ensure user-installed Python packages are always found (needed when run from cron)
export PYTHONPATH="/home/kartikp-home-ubuntu/.local/lib/python3.12/site-packages:${PYTHONPATH:-}"

# Use a lock file to prevent overlapping runs
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SKIP] Another health-check is already running." >> "$LOG_FILE"
    exit 0
fi

{
    # Check if the server responds on port 5000 via HTTP
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 http://localhost:5000/ 2>/dev/null)

    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "304" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] Server is healthy (HTTP $HTTP_STATUS)."
        exit 0
    fi

    # Server did not respond — clean up stale PID file if present
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARN] Server is not responding (HTTP status: '${HTTP_STATUS}'). Restarting..."
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        kill "$OLD_PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Killed stale process (PID: $OLD_PID)."
    fi

    # Restart the server
    bash "$SCRIPT_DIR/start.sh" >> "$LOG_FILE" 2>&1
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [OK] Server restarted successfully."
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] Server failed to restart. Check server.log for details."
    fi
} >> "$LOG_FILE" 2>&1
