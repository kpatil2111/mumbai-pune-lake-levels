#!/bin/bash

# Stop script for MWRD Lake Levels Dashboard
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "ℹ No PID file found. Is the server running?"
    # Try to find and kill any stray app.py processes anyway
    STRAY=$(pgrep -f "python3 app.py" 2>/dev/null)
    if [ -n "$STRAY" ]; then
        echo "  Found stray process(es): $STRAY — stopping them."
        kill $STRAY
        echo "✓ Stopped."
    fi
    exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
    echo "🛑 Stopping MWRD Lake Levels Dashboard (PID: $PID)..."
    kill "$PID"

    # Wait up to 5 seconds for graceful shutdown
    for i in $(seq 1 5); do
        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi
        sleep 1
    done

    # Force kill if still running
    if kill -0 "$PID" 2>/dev/null; then
        echo "  Process did not exit; sending SIGKILL..."
        kill -9 "$PID"
    fi

    echo "✓ Server stopped."
else
    echo "ℹ Process $PID is not running (stale PID file)."
fi

rm -f "$PID_FILE"
