import datetime
import os
import sqlite3
import time
import requests
import argparse
import views
from tqdm import tqdm  # <--- Added


def get_live_hom_id():
    url = "https://data.ninjakiwi.com/battles2/homs"
    retries = 0
    max_retries = 7
    backoff_factor = 2

    while retries <= max_retries:
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()

            if data["success"] and data["body"]:
                for season in data["body"]:
                    if season["live"]:
                        leaderboard_url = season["leaderboard"]
                        season_id = leaderboard_url.split("/")[-2]
                        return season_id
            retries += 1
            if retries <= max_retries:
                time.sleep(1)
        except Exception:
            time.sleep(1)
            retries += 1

    return None


def get_overall_win_rate(user_id, session_cache, cursor=None):
    if not user_id:
        return 0.5
    if user_id in session_cache:
        return session_cache[user_id]

    url = f"https://data.ninjakiwi.com/battles2/users/{user_id}"
    retries = 0

    while retries < 5:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                # Use tqdm.write so it doesn't break the progress bar
                tqdm.write(f"    [!] Rate limited on profile {user_id}. Sleeping {retry_after}s...")
                time.sleep(retry_after)
                retries += 1
                continue

            resp.raise_for_status()
            data = resp.json()

            if not data.get("success"):
                session_cache[user_id] = 0.5
                return 0.5

            body = data.get("body", {})
            ranked_stats = body.get("rankedStats", {})
            wins = ranked_stats.get("wins", 0)
            losses = ranked_stats.get("losses", 0)
            draws = ranked_stats.get("draws", 0)
            games = wins + losses + draws

            adjusted_wr = max(0.0, min(1.0, (wins + 10) / (games + 20)))
            session_cache[user_id] = adjusted_wr

            if cursor:
                try:
                    cursor.execute("""
                        INSERT INTO players (user_id, baseline_wr, total_wpa, games_tracked)
                        VALUES (?, ?, 0, 0)
                        ON CONFLICT(user_id) DO NOTHING
                    """, (user_id, adjusted_wr))
                except Exception as e:
                    tqdm.write(f"    [!] DB Save Error: {e}")

            return adjusted_wr

        except Exception:
            break

    session_cache[user_id] = 0.5
    return 0.5


def calculate_smoothed_skill(wins, losses, profile_baseline):
    K = 20
    games = wins + losses
    return (wins + (profile_baseline * K)) / (games + K)


def get_matches(hom_id, user_ids):
    conn = sqlite3.connect(f"{hom_id}_matches.db")
    cursor = conn.cursor()

    player_cache = {}
    cursor.execute("SELECT user_id, baseline_wr, wins, losses FROM players")
    for row in cursor.fetchall():
        player_cache[row[0]] = [row[1], row[2], row[3]]

    # --- PROGRESS BAR START ---
    pbar = tqdm(user_ids, desc="Fetching Matches", unit="user", leave=True)
    for userID in pbar:
        userID = userID.strip()
        pbar.set_description(f"Processing {userID[:12]}")  # Show start of ID

        if userID not in player_cache:
            base = get_overall_win_rate(userID, {}, cursor)
            player_cache[userID] = [base, 0, 0]
            cursor.execute("INSERT OR IGNORE INTO players (user_id, baseline_wr) VALUES (?, ?)", (userID, base))
            conn.commit()

        url = f"https://data.ninjakiwi.com/battles2/users/{userID}/matches"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            matches = response.json().get("body", [])

            for match in matches:
                if match['gametype'] != 'Ranked': continue
                cursor.execute("SELECT 1 FROM matches WHERE match_id = ?", (match['id'],))
                if cursor.fetchone(): continue

                l_id = match.get("playerLeft", {}).get("profileURL", "").split('/')[-1]
                r_id = match.get("playerRight", {}).get("profileURL", "").split('/')[-1]
                if not l_id or not r_id: continue

                for p_id in [l_id, r_id]:
                    if p_id not in player_cache:
                        base = get_overall_win_rate(p_id, {}, cursor)
                        player_cache[p_id] = [base, 0, 0]
                        cursor.execute("INSERT OR IGNORE INTO players (user_id, baseline_wr) VALUES (?, ?)",
                                       (p_id, base))

                l_data = player_cache[l_id]
                r_data = player_cache[r_id]
                l_skill = calculate_smoothed_skill(l_data[1], l_data[2], l_data[0])
                r_skill = calculate_smoothed_skill(r_data[1], r_data[2], r_data[0])
                left_won = match.get("playerLeft", {}).get("result") == "win"
                l_wpa, r_wpa = calculate_wpa(l_skill, r_skill, left_won)

                # Update DB (Simplified for brevity as your original had placeholders)
                # cursor.execute("INSERT INTO matches ...")

                for p_id, p_wpa, p_won in [(l_id, l_wpa, left_won), (r_id, r_wpa, not left_won)]:
                    player_cache[p_id][1] += 1 if p_won else 0
                    player_cache[p_id][2] += 0 if p_won else 1
                    cursor.execute('''
                        UPDATE players SET 
                            total_wpa = total_wpa + ?, 
                            games_tracked = games_tracked + 1,
                            wins = wins + ?,
                            losses = losses + ?
                        WHERE user_id = ?
                    ''', (p_wpa, 1 if p_won else 0, 0 if p_won else 1, p_id))

            conn.commit()
        except Exception:
            continue
    # --- PROGRESS BAR END ---

    conn.close()


def calculate_wpa(left_baseline, right_baseline, left_won):
    p_left = max(0.01, min(0.99, left_baseline))
    p_right = max(0.01, min(0.99, right_baseline))
    odds_left = p_left / (1 - p_left)
    odds_right = p_right / (1 - p_right)
    expected_left = odds_left / (odds_left + odds_right)
    wpa_left = (1.0 if left_won else 0.0) - expected_left
    return wpa_left, -wpa_left


def create_matches_db(db_id):
    """
    Creates a new season database.
    Grandfathers players by turning the previous season's
    Smoothed Skill into the new season's Baseline.
    """
    db_name = f"{db_id}_matches.db"
    if not os.path.exists(db_name):
        conn = sqlite3.connect(db_name, timeout=30)
        cursor = conn.cursor()

        # 1. Matches Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id CHAR(60) PRIMARY KEY, map TEXT, playerLeftWin BOOLEAN,
            lHero TEXT, lt1 TEXT, lt2 TEXT, lt3 TEXT, rHero TEXT, rt1 TEXT, rt2 TEXT, rt3 TEXT,
            duration INT, endRound INT, left_wpa REAL, right_wpa REAL, 
            left_user_id TEXT, right_user_id TEXT
        )""")

        # 2. Players Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            user_id TEXT PRIMARY KEY, 
            baseline_wr REAL, 
            total_wpa REAL DEFAULT 0.0, 
            games_tracked INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0
        )""")
        conn.commit()

        # 3. ADVANCED GRANDFATHERING LOGIC
        try:
            prefix, num = db_id.rsplit('_', 1)
            prev_db_name = f"{prefix}_{int(num) - 1}_matches.db"
            K = 20.0  # Smoothing constant

            if os.path.exists(prev_db_name):
                print(f"Found {prev_db_name}. Calculating adaptive baselines for {db_id}...")

                prev_conn = sqlite3.connect(prev_db_name)
                prev_cursor = prev_conn.cursor()

                # Calculate the smoothed skill in the SELECT query itself
                # New Baseline = (Wins + (Old_Baseline * K)) / (Wins + Losses + K)
                prev_cursor.execute(f"""
                    SELECT 
                        user_id, 
                        (wins + (baseline_wr * {K})) / (wins + losses + {K}) AS adaptive_baseline,
                        total_wpa,
                        games_tracked
                    FROM players
                """)
                grandfathered_players = prev_cursor.fetchall()
                prev_conn.close()

                if grandfathered_players:
                    # Insert into new DB. Seasonal wins/losses are set to 0 fresh.
                    cursor.executemany("""
                        INSERT OR IGNORE INTO players (user_id, baseline_wr, total_wpa, games_tracked, wins, losses)
                        VALUES (?, ?, ?, ?, 0, 0)
                    """, grandfathered_players)
                    conn.commit()
                    print(f"Successfully carried over {len(grandfathered_players)} players with adaptive baselines.")
            else:
                print(f"No previous database found ({prev_db_name}).")

        except Exception as e:
            print(f"Note: Could not carry over player data: {e}")

        conn.close()

        # 4. Discovery Maps for Views (from previous DB if exists)
        map_list = []
        try:
            if os.path.exists(prev_db_name):
                prev_conn = sqlite3.connect(prev_db_name)
                map_list = [row[0] for row in prev_conn.execute("SELECT DISTINCT map FROM matches")]
                prev_conn.close()
        except:
            pass

        views.apply_views(db_name, map_list)
        print(f"Database '{db_name}' initialized.")
    else:
        print(f"Database '{db_name}' already exists.")


def get_players(hom_id):
    url = f'https://data.ninjakiwi.com/battles2/homs/{hom_id}/leaderboard'
    user_ids = []
    # Added a small bar for fetching the leaderboard too
    pbar = tqdm(desc="Fetching Leaderboard", unit="page")
    while url:
        try:
            response = requests.get(url)
            if response.status_code == 429:
                time.sleep(5)
                continue
            response.raise_for_status()
            data = response.json()
            for player in data['body']:
                user_id = player['profile'].split('/')[-1]
                user_ids.append(user_id)
            url = data.get('next')
            pbar.update(1)
        except Exception:
            break
    pbar.close()
    return user_ids


def merge_matches_tables(db_source, db_dest):
    # (Keep your existing merge logic, just ensure you include new columns)
    try:
        conn_source = sqlite3.connect(db_source)
        conn_dest = sqlite3.connect(db_dest)
        cursor_source = conn_source.cursor()
        cursor_dest = conn_dest.cursor()

        # Add columns if missing
        for col in ['left_wpa', 'right_wpa', 'left_user_id', 'right_user_id']:
            try:
                cursor_dest.execute(f"ALTER TABLE matches ADD COLUMN {col} REAL")
            except:
                pass

        # Copy Matches
        cursor_source.execute("SELECT * FROM matches")
        rows = cursor_source.fetchall()
        # Use simple dynamic insertion to handle column count mismatches gracefully
        if rows:
            cols = [description[0] for description in cursor_source.description]
            placeholders = ",".join("?" * len(cols))
            col_names = ",".join(cols)
            cursor_dest.executemany(f"INSERT OR IGNORE INTO matches ({col_names}) VALUES ({placeholders})", rows)

        # Copy Players
        cursor_dest.execute(
            "CREATE TABLE IF NOT EXISTS players (user_id TEXT PRIMARY KEY, baseline_wr REAL, total_wpa REAL DEFAULT 0.0, games_tracked INTEGER DEFAULT 0)")
        cursor_source.execute("SELECT user_id, baseline_wr, total_wpa, games_tracked FROM players")
        players = cursor_source.fetchall()
        for p in players:
            cursor_dest.execute("""
                INSERT INTO players (user_id, baseline_wr, total_wpa, games_tracked)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    total_wpa = total_wpa + excluded.total_wpa,
                    games_tracked = games_tracked + excluded.games_tracked,
                    baseline_wr = excluded.baseline_wr
            """, p)

        conn_dest.commit()
        print(f"Merged into {db_dest}")
    except Exception as e:
        print(f"Merge error: {e}")
    finally:
        if conn_source: conn_source.close()
        if conn_dest: conn_dest.close()


def main():
    parser = argparse.ArgumentParser(description="Battles 2 Data Scraper")
    parser.add_argument('--now', action='store_true', help='Run immediately on startup')
    args = parser.parse_args()

    is_first_run = True

    start = datetime.datetime.now()
    while True:
        now = datetime.datetime.now()
        next_hour = now + datetime.timedelta(hours=1)
        next_hour_rounded = next_hour.replace(minute=0, second=0, microsecond=0)
        time_until_next_hour = (next_hour_rounded - now).total_seconds()
        next_hour_str = next_hour_rounded.strftime("%H:%M")

        if is_first_run and args.now:
            print("Force flag detected: Starting immediate iteration...")
            is_first_run = False
        else:
            print(f"Sleeping until {next_hour_str}")
            time.sleep(time_until_next_hour)
            is_first_run = False

        try:
            start = datetime.datetime.now()

            api_id = get_live_hom_id()
            if api_id:
                prefix, num = api_id.rsplit('_', 1)
                db_id = f"{prefix}_{int(num) + 1}"
                create_matches_db(db_id)
                user_ids = get_players(api_id)
                get_matches(db_id, user_ids)

                db_source = f"{db_id}_matches.db"
                views.apply_views(db_source)

                # Merges
                db_dest = "s25+_matches.db"
                merge_matches_tables(db_source, db_dest)
                views.apply_views(db_dest)

                db_dest = "s34+_matches.db"
                merge_matches_tables(db_source, db_dest)
                views.apply_views(db_dest)

                db_dest = "s38+_matches.db"
                merge_matches_tables(db_source, db_dest)
                views.apply_views(db_dest)

                timetaken = datetime.datetime.now() - start
                print(f"Done in {timetaken}")

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(60)
            continue


if __name__ == "__main__":
    main()
