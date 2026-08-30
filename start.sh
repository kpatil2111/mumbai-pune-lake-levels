#!/bin/bash

# Start script for MWRD Lake Levels Dashboard
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
PID_FILE="$SCRIPT_DIR/server.pid"
LOG_FILE="$SCRIPT_DIR/server.log"

# Ensure user-installed Python packages (flask, psycopg2, etc.) are found
# even when launched from cron or non-login shells.
export PYTHONPATH="/home/kartikp-home-ubuntu/.local/lib/python3.12/site-packages:${PYTHONPATH:-}"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "✓ Server is already running (PID: $PID)"
        echo "  Dashboard: http://localhost:5000"
        exit 0
    else
        # Stale PID file, remove it
        rm "$PID_FILE"
    fi
fi

echo "🚀 Starting MWRD Lake Levels Dashboard..."

# Launch the Flask app from within the backend directory
cd "$BACKEND_DIR"
nohup python3 app.py > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo "$SERVER_PID" > "$PID_FILE"

# Wait briefly and confirm the server started
sleep 3

if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✓ Server started successfully!"
    echo "  PID:       $SERVER_PID"
    echo "  Dashboard: http://localhost:5000"
    echo "  Logs:      $LOG_FILE"
else
    echo "✗ Server failed to start. Check logs:"
    cat "$LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
