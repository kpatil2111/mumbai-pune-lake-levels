import os
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory
from scraper import get_current_lake_levels
from db import init_db, get_all_history, save_dams_reading

app = Flask(__name__, static_folder="../frontend")

DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# Core target dams list for consistent tracking
TARGET_DAMS_LIST = [
    {"name": "Khadakwasla", "region": "pune", "live_storage_designed": 55.91},
    {"name": "Panshet", "region": "pune", "live_storage_designed": 301.61},
    {"name": "Warasgaon", "region": "pune", "live_storage_designed": 363.13},
    {"name": "Temghar", "region": "pune", "live_storage_designed": 105.01},
    {"name": "Pawana", "region": "pune", "live_storage_designed": 274.32},
    {"name": "Bhama Askhed", "region": "pune", "live_storage_designed": 217.10},
    {"name": "Upper Vaitarna", "region": "mumbai", "live_storage_designed": 331.31},
    {"name": "Middle Vaitarna", "region": "mumbai", "live_storage_designed": 193.53},
    {"name": "Modak Sagar", "region": "mumbai", "live_storage_designed": 174.79},
    {"name": "Tansa", "region": "mumbai", "live_storage_designed": 172.52},
    {"name": "Bhatsa", "region": "mumbai", "live_storage_designed": 942.10}
]

def seed_historical_data():
    """Generates realistic historical data for the last 30 days if not present."""
    history = get_all_history()
    if history:
        return

    print("Seeding historical lake level data...")
    # We will generate data for the past 30 days up to yesterday
    today = datetime.now()
    
    for i in range(30, 0, -1):
        date_obj = today - timedelta(days=i)
        date_str = date_obj.strftime("%d/%m/%Y")
        
        # Calculate a factor that simulates lake levels starting low (e.g. end of May)
        # and gradually rising as monsoons begin in June.
        # Days go from -30 to -1. Let's make a rising factor from 0.08 (8%) to today's levels.
        progress = (30 - i) / 30.0  # 0.0 to 1.0
        
        day_dams = []
        for dam in TARGET_DAMS_LIST:
            designed = dam["live_storage_designed"]
            # Target percentage (today's actual or standard average)
            # Khadakwasla: ~20%, Panshet: ~17%, Warasgaon: ~11%, Temghar: ~0%, Pawana: ~16%, Bhama Askhed: ~28%
            # Vaitarna: ~34%, Middle Vaitarna: ~10%, Modak Sagar: ~41%, Tansa: ~17%, Bhatsa: ~29%
            if dam["name"] == "Khadakwasla":
                target_pct = 20.30
            elif dam["name"] == "Panshet":
                target_pct = 17.71
            elif dam["name"] == "Warasgaon":
                target_pct = 11.78
            elif dam["name"] == "Temghar":
                target_pct = 2.0  # Start slightly above 0 for simulation
            elif dam["name"] == "Pawana":
                target_pct = 16.63
            elif dam["name"] == "Bhama Askhed":
                target_pct = 28.90
            elif dam["name"] == "Upper Vaitarna":
                target_pct = 34.37
            elif dam["name"] == "Middle Vaitarna":
                target_pct = 10.78
            elif dam["name"] == "Modak Sagar":
                target_pct = 41.86
            elif dam["name"] == "Tansa":
                target_pct = 17.86
            elif dam["name"] == "Bhatsa":
                target_pct = 29.03
            else:
                target_pct = 20.0
            
            # Start percentage at start of 30 days is lower (e.g. 5% to 15%)
            start_pct = max(3.0, target_pct * 0.4)
            # Interpolate between start and today
            current_pct = start_pct + (target_pct - start_pct) * progress
            current_live = (current_pct / 100.0) * designed
            
            day_dams.append({
                "name": dam["name"],
                "region": dam["region"],
                "live_storage_today": round(current_live, 2),
                "percentage_today": round(current_pct, 2),
                "percentage_last_year": round(target_pct * 1.2, 2)  # dummy last year comparison
            })
            
        save_dams_reading(date_str, day_dams)
    print("Historical data seeded successfully.")

def save_current_to_history(current_data):
    """Appends current scraped data to the history file if not already present for that date."""
    if not current_data:
        return False
        
    # Get the date of the scraped report (e.g., "25/06/2026")
    report_date = current_data[0]["date"]
    
    try:
        # Build entry
        dams_entry = []
        for dam in current_data:
            dams_entry.append({
                "name": dam["name"],
                "region": dam["region"],
                "live_storage_today": dam["live_storage_today"],
                "percentage_today": dam["percentage_today"],
                "percentage_last_year": dam["percentage_last_year"]
            })
            
        return save_dams_reading(report_date, dams_entry)
    except Exception as e:
        print(f"Error saving today's data to database: {e}")
        return False

# NOTE: seed_historical_data() is intentionally NOT called here.
# Only real scraped data is stored in history.json.

# Try to run database initialization on startup
try:
    init_db()
except Exception as e:
    print(f"Failed to initialize database on startup: {e}")

# Try to run an initial scrape to update history with today's real numbers
try:
    print("Running initial MWRD scrape on startup...")
    current_levels = get_current_lake_levels()
    if current_levels:
        save_current_to_history(current_levels)
        print("Initial startup scrape and save successful.")
except Exception as e:
    print(f"Failed initial startup scrape: {e}")

@app.route("/api/lake-levels", methods=["GET"])
def get_lake_levels():
    """Serves the full historical timeline and current levels."""
    try:
        history = get_all_history()
        # Current data is the last entry in the history
        current = history[-1] if history else {}
        
        return jsonify({
            "success": True,
            "history": history,
            "current": current
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/refresh", methods=["POST"])
def refresh_data():
    """Triggers scraping of latest PDF and appends to history."""
    current_levels = get_current_lake_levels()
    if not current_levels:
        return jsonify({"success": False, "error": "Could not fetch or parse PDF from MWRD"}), 500
        
    saved = save_current_to_history(current_levels)
    if not saved:
        return jsonify({"success": False, "error": "Failed to save data to database"}), 500
        
    history = get_all_history()
        
    return jsonify({
        "success": True,
        "history": history,
        "current": history[-1] if history else {}
    })

# Serve Frontend Static Assets
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == "__main__":
    # Ensure database is initialized
    try:
        init_db()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
    # Ensure directories exist
    os.makedirs(os.path.join(os.path.dirname(__file__), "../data"), exist_ok=True)
    os.makedirs(app.static_folder, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
