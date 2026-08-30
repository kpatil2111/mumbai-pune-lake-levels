import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file relative to db.py
db_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(db_dir, ".env")
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:kartikp001@localhost:5432/lake_levels")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """Initializes the PostgreSQL database schema if not already present."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS dam_history (
                    id SERIAL PRIMARY KEY,
                    reading_date DATE NOT NULL,
                    dam_name VARCHAR(100) NOT NULL,
                    region VARCHAR(50) NOT NULL,
                    live_storage_today DOUBLE PRECISION NOT NULL,
                    percentage_today DOUBLE PRECISION NOT NULL,
                    percentage_last_year DOUBLE PRECISION NOT NULL,
                    UNIQUE(reading_date, dam_name)
                );
            """)
        conn.commit()
    finally:
        conn.close()

def save_dams_reading(date_str, dams_data):
    """
    Saves or updates readings for a specific date in the PostgreSQL database.
    dams_data is a list of dicts like:
    {
        "name": ...,
        "region": ...,
        "live_storage_today": ...,
        "percentage_today": ...,
        "percentage_last_year": ...
    }
    """
    if not dams_data:
        return False
        
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return False

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for dam in dams_data:
                cur.execute("""
                    INSERT INTO dam_history (
                        reading_date, dam_name, region, 
                        live_storage_today, percentage_today, percentage_last_year
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (reading_date, dam_name) DO UPDATE SET
                        region = EXCLUDED.region,
                        live_storage_today = EXCLUDED.live_storage_today,
                        percentage_today = EXCLUDED.percentage_today,
                        percentage_last_year = EXCLUDED.percentage_last_year
                """, (
                    date_obj,
                    dam["name"],
                    dam["region"],
                    dam["live_storage_today"],
                    dam["percentage_today"],
                    dam["percentage_last_year"]
                ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving dams reading to database: {e}")
        return False
    finally:
        conn.close()

def get_all_history():
    """
    Retrieves the full historical timeline from PostgreSQL, grouped chronologically.
    Returns a format identical to the original JSON history structure.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT reading_date, dam_name, region, 
                       live_storage_today, percentage_today, percentage_last_year
                FROM dam_history
                ORDER BY reading_date ASC, dam_name ASC
            """)
            rows = cur.fetchall()
            
            # Group by date
            from collections import defaultdict
            history_dict = defaultdict(list)
            for r in rows:
                date_str = r[0].strftime("%d/%m/%Y")
                history_dict[date_str].append({
                    "name": r[1],
                    "region": r[2],
                    "live_storage_today": r[3],
                    "percentage_today": r[4],
                    "percentage_last_year": r[5]
                })
            
            # Sort date strings chronologically
            sorted_dates = sorted(history_dict.keys(), key=lambda d: datetime.strptime(d, "%d/%m/%Y"))
            
            history_list = []
            for date_str in sorted_dates:
                history_list.append({
                    "date": date_str,
                    "dams": history_dict[date_str]
                })
            return history_list
    except Exception as e:
        print(f"Error querying database history: {e}")
        return []
    finally:
        conn.close()
