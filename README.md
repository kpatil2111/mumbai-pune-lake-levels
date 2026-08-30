# MWRD Pravah Dashboard 💧

A real-time **Maharashtra reservoir water storage dashboard** that scrapes the daily PDF report published by the [Maharashtra Water Resources Department (MWRD)](https://mwrdpravah.in) and presents live and historical storage levels for key Pune and Mumbai water supply reservoirs.

---

## Features

- **Live Data Scraping** — downloads the latest MWRD daily PDF report, parses dam storage data, and persists it to PostgreSQL
- **Regional Overview Cards** — at-a-glance average live storage % and volume for Pune and Mumbai regions
- **30-Day Trend Chart** — line chart showing daily storage percentage over the past month for both regions
- **Individual Reservoir Cards** — per-dam storage %, live vs. designed capacity, and YoY comparison
- **Region Filter** — toggle between All Reservoirs, Pune Region, and Mumbai Supply
- **One-click Sync** — refresh button triggers a new MWRD PDF fetch and updates the dashboard instantly
- **Automated Cron Sync** — daily cron script keeps the database updated hands-free
- **Flask + Vanilla JS** — lightweight Python backend serving a static frontend

---

## Tracked Reservoirs

| Region | Reservoir | Designed Capacity (Mcum) |
|---|---|---|
| Pune | Khadakwasla | 55.91 |
| Pune | Panshet | 301.61 |
| Pune | Warasgaon | 363.13 |
| Pune | Temghar | 105.01 |
| Pune | Pawana | 274.32 |
| Pune | Bhama Askhed | 217.10 |
| Mumbai | Upper Vaitarna | 331.31 |
| Mumbai | Middle Vaitarna | 193.53 |
| Mumbai | Modak Sagar | 174.79 |
| Mumbai | Tansa | 172.52 |
| Mumbai | Bhatsa | 942.10 |

---

## Architecture

```
lake-levels/
├── backend/
│   ├── app.py          # Flask app — REST API + static file serving
│   ├── scraper.py      # Downloads & parses the MWRD daily PDF
│   ├── db.py           # PostgreSQL helpers (init, read, upsert)
│   ├── migrate.py      # DB migration utility
│   ├── requirements.txt
│   ├── .env            # Your local DB credentials (git-ignored)
│   └── .env.template   # Copy this to create .env
├── frontend/
│   ├── index.html      # Dashboard UI
│   ├── app.js          # Chart rendering, API calls, dynamic cards
│   └── style.css       # Glassmorphism design system
├── data/               # Optional JSON backup (legacy)
├── start.sh            # Start the Flask server in the background
├── stop.sh             # Stop the background Flask server
├── sync-lake-levels.sh # Cron-safe sync script
├── healthcheck.sh      # Service liveness check
└── CRON.md             # Cron setup instructions
```

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/lake-levels` | Returns full historical timeline + current day data |
| `POST` | `/api/refresh` | Triggers a new MWRD PDF scrape and saves results |
| `GET` | `/` | Serves the frontend dashboard |

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (running locally or on a server)
- `pip` / virtual environment tooling

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url> lake-levels
cd lake-levels
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Create the PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE lake_levels;"
```

### 5. Configure environment variables

```bash
cp backend/.env.template backend/.env
```

Edit `backend/.env` and set your database credentials:

```env
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/lake_levels
```

### 6. Initialise the database schema

The schema is created automatically when the Flask app starts for the first time. You can also run it manually:

```bash
cd backend
python3 -c "from db import init_db; init_db(); print('DB initialised')"
```

---

## Running the App

### Development (foreground, with debug output)

```bash
cd backend
python3 app.py
```

Open **http://localhost:5000** in your browser.

### Production (background daemon)

Use the provided helper scripts from the project root:

```bash
# Start
./start.sh

# Check if running
./healthcheck.sh

# Stop
./stop.sh
```

Logs are written to `server.log` in the project root. The server PID is stored in `server.pid`.

---

## Data Sync

On startup, the Flask app automatically fetches the latest MWRD PDF and saves the data to the database.

To manually trigger a sync while the server is running, click the **🔄 Sync Latest PDF** button in the dashboard, or call the API directly:

```bash
curl -X POST http://localhost:5000/api/refresh
```

### Automated Daily Sync (Cron)

Set up the included cron script to sync every day automatically. The script is safe to run from cron — it uses a lock file to prevent overlapping runs.

```bash
# Edit your crontab
crontab -e
```

Add this line to sync at 10:00 AM IST every day:

```cron
0 10 * * * /path/to/lake-levels/sync-lake-levels.sh
```

Sync logs are written to `sync.log`. See [`CRON.md`](CRON.md) for more details.

---

## Data Source

All data is sourced from the **Maharashtra Water Resources Department (MWRD)** daily dam safety report:

- **URL**: https://mwrdpravah.in/damsafety/control/pdfLatestReportEng
- **Format**: PDF, published daily
- **Fields extracted**: Dam name, report date & time, dead storage, designed live storage, today's live storage, % filled today, % filled last year

> **Note**: The MWRD site uses a self-signed SSL certificate. The scraper suppresses the resulting SSL warnings with `urllib3.disable_warnings()` — this is expected behaviour.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| Database | PostgreSQL + psycopg2 |
| PDF Parsing | pypdf |
| Frontend | Vanilla HTML / CSS / JavaScript |
| Charts | Chart.js |
| Fonts | Outfit (Google Fonts) |
| Process management | Bash scripts (`start.sh`, `stop.sh`) |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `psycopg2` connection error | Check that PostgreSQL is running and `DATABASE_URL` in `.env` is correct |
| PDF scrape returns empty list | MWRD may not have published today's report yet; try again after 09:00 IST |
| Server won't start (port in use) | Run `./stop.sh` first, or `kill $(cat server.pid)` |
| Cron sync not working | Check `sync.log`; ensure the script path is absolute and executable (`chmod +x sync-lake-levels.sh`) |
