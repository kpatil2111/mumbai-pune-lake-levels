#!/bin/bash

# Cron-friendly sync script for MWRD Lake Levels Dashboard.
# Fetches the latest MWRD PDF and upserts the report date into data/history.json.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
DATA_DIR="$SCRIPT_DIR/data"
LOG_FILE="$SCRIPT_DIR/sync.log"
LOCK_FILE="/tmp/lake-levels-sync.lock"

mkdir -p "$DATA_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Another lake levels sync is already running." >> "$LOG_FILE"
    exit 0
fi

{
    echo "----- $(date '+%Y-%m-%d %H:%M:%S') Starting lake levels sync -----"

    cd "$BACKEND_DIR"

    python3 - <<'PY'
import sys
from scraper import get_current_lake_levels
from db import save_dams_reading

current_data = get_current_lake_levels()
if not current_data:
    raise SystemExit("Could not fetch or parse latest MWRD report.")

report_date = current_data[0]["date"]

dams_entry = [
    {
        "name": dam["name"],
        "region": dam["region"],
        "live_storage_today": dam["live_storage_today"],
        "percentage_today": dam["percentage_today"],
        "percentage_last_year": dam["percentage_last_year"],
    }
    for dam in current_data
]

success = save_dams_reading(report_date, dams_entry)
if not success:
    raise SystemExit("Failed to save synced data to PostgreSQL database.")

print(f"Successfully synced lake levels to PostgreSQL for {report_date}. Dams synced: {len(dams_entry)}")
PY

    echo "----- $(date '+%Y-%m-%d %H:%M:%S') Lake levels sync finished -----"
} >> "$LOG_FILE" 2>&1
