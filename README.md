# Bloonalytics — Bloons TD Battles 2 Stats Platform

A data analytics platform for **Bloons TD Battles 2** that scrapes match data from the Ninja Kiwi API, computes **Win Probability Added (WPA)** for players, and serves interactive statistics via [Datasette](https://datasette.io/).

## Overview

- **Scraper** (`wpa.py`) — Fetches match data from the [Ninja Kiwi API](https://data.ninjakiwi.com/battles2) and stores it in season-partitioned SQLite databases (e.g. `season_40_matches.db`).
- **Views** (`views.py`) — Creates SQL views for heroes, towers, loadouts, hero-loadout combos, and maps with WPA, pick rates, and 95% confidence intervals.
- **Server** (`ds.py`) — Launches Datasette to serve the databases with a custom config.
- **Dashboard** (`bloonalytics-dashboard/`) — A React + Vite frontend for browsing stats.
- **Custom Queries** — Pre-built SQL queries for win/loss by round, winrate by round, counter loadouts, and loadout experts.

## Data Schema

### `matches` table
| Column | Type | Description |
|---|---|---|
| `match_id` | TEXT PK | Unique match identifier |
| `map` | TEXT | Map name |
| `playerLeftWin` | BOOL | Whether the left player won |
| `lHero`, `rHero` | TEXT | Left/right hero |
| `lt1`–`lt3`, `rt1`–`rt3` | TEXT | Left/right tower loadout (sorted) |
| `duration` | INT | Match duration in seconds |
| `endRound` | INT | Final round reached |
| `left_wpa`, `right_wpa` | REAL | Win probability added |
| `left_user_id`, `right_user_id` | TEXT | Player IDs |

### `players` table
| Column | Type | Description |
|---|---|---|
| `user_id` | TEXT PK | Player ID |
| `baseline_wr` | REAL | Baseline win rate (seeded from previous season or API) |
| `total_wpa` | REAL | Cumulative WPA across tracked games |
| `games_tracked` | INT | Number of games tracked |
| `wins`, `losses` | INT | Win/loss count |

### WPA Calculation
WPA uses a smoothed ELO-style estimate: expected win probability is derived from the ratio of smoothed skill ratings (with K=20), and WPA is the difference between actual outcome and expected probability.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for the dashboard)

### Setup and Run

```bash
# Install Python dependencies
pip install datasette sqlite-utils requests tqdm

# Initialize a season database (auto-run by scraper)
python wpa.py --now

# Launch the Datasette server
python ds.py
```

The Datasette server runs at `http://localhost:8001` by default.

### Dashboard

```bash
cd bloonalytics-dashboard
npm install
npm run dev
```

## Usage

The scraper runs on an hourly loop, fetching the latest Hall of Masters leaderboard and match data. Season databases are created automatically when a new HOM season is detected.

Datasette exposes:
- **SQL views** for global and per-map hero/tower/loadout stats
- **Custom queries** for win/loss distribution, winrate by round, counter loadouts, and loadout experts
- **Player rankings** with a custom ELO formula

## Project Structure

```
battles2/
├── wpa.py                   # Scraper: fetches matches, computes WPA
├── views.py                 # SQL view definitions
├── ds.py                    # Datasette launcher
├── datasette.yaml           # Datasette configuration
├── templates/index.html     # Root template
├── static/                  # Static assets (icons, CSS)
├── bloonalytics-dashboard/  # React frontend
├── *+*.db                   # Merged season databases
├── season_*_matches.db      # Individual season databases
└── secrets/                 # (gitignored) API keys
```
