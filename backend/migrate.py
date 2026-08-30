import os
import json
import sys
from db import init_db, save_dams_reading

def main():
    print("Starting database migration...")
    
    # 1. Initialize DB schema
    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        sys.exit(1)
        
    # 2. Check for history.json path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    history_file = os.path.join(backend_dir, "../data/history.json")
    
    if not os.path.exists(history_file):
        print(f"Error: Historical data file not found at {history_file}")
        sys.exit(1)
        
    # 3. Read history.json
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON history file: {e}")
        sys.exit(1)
        
    print(f"Found {len(history_data)} daily records to migrate.")
    
    # 4. Migrate records
    migrated_count = 0
    failed_count = 0
    
    for entry in history_data:
        date_str = entry.get("date")
        dams = entry.get("dams", [])
        
        if not date_str or not dams:
            print(f"Skipping malformed entry: {entry}")
            continue
            
        success = save_dams_reading(date_str, dams)
        if success:
            migrated_count += 1
        else:
            print(f"Failed to migrate record for date: {date_str}")
            failed_count += 1
            
    print("\n--- Migration Summary ---")
    print(f"Successfully migrated: {migrated_count} days")
    print(f"Failed migration:     {failed_count} days")
    
    if failed_count > 0:
        sys.exit(1)
    else:
        print("Migration completed successfully!")

if __name__ == "__main__":
    main()
