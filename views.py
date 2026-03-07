import glob
import sqlite3
import sqlite_utils
import os


def global_views(db_path):
    """
    Creates SQL views in the specified SQLite database.
    """
    db = sqlite_utils.Database(db_path)

    # Heroes view
    try:
        db.create_view(
            "all_heroes",
            """
WITH MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM matches
),
Unpivoted AS (
    SELECT 
        CASE n.id 
            WHEN 1 THEN m.lHero 
            ELSE m.rHero 
        END AS Hero,
        CASE 
            WHEN n.id = 1 THEN m.playerLeftWin 
            ELSE NOT m.playerLeftWin 
        END AS Win,
        CASE 
            WHEN n.id = 1 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM matches m
    CROSS JOIN (SELECT 1 AS id UNION ALL SELECT 2) n
),
Aggregated AS (
    SELECT 
        Hero,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY Hero
)
SELECT 
    Hero,
    'https://b2.kozow.com/static/' || Hero || '.png' AS Icon,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
    """
        )
    except:
        pass

    # Towers view
    try:
        db.create_view(
            "all_towers",
            """
WITH MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM matches
),
Unpivoted AS (
    SELECT 
        CASE n.id
            WHEN 1 THEN m.lt1 WHEN 2 THEN m.lt2 WHEN 3 THEN m.lt3
            WHEN 4 THEN m.rt1 WHEN 5 THEN m.rt2 WHEN 6 THEN m.rt3
        END AS Tower,
        CASE 
            WHEN n.id <= 3 THEN m.playerLeftWin 
            ELSE NOT m.playerLeftWin 
        END AS Win,
        CASE 
            WHEN n.id <= 3 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM matches m
    CROSS JOIN (
        SELECT 1 AS id UNION ALL SELECT 2 UNION ALL SELECT 3 
        UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
    ) n
),
Aggregated AS (
    SELECT 
        Tower,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY Tower
)
SELECT 
    Tower,
    'https://b2.kozow.com/static/' || Tower || '.png' AS Icon,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
            """
        )
    except:
        pass

    # loadouts view
    try:
        db.create_view(
            "all_loadouts",
            """
WITH MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM matches
),
Unpivoted AS (
    SELECT 
        CASE n.id WHEN 1 THEN m.lt1 ELSE m.rt1 END AS T1,
        CASE n.id WHEN 1 THEN m.lt2 ELSE m.rt2 END AS T2,
        CASE n.id WHEN 1 THEN m.lt3 ELSE m.rt3 END AS T3,
        CASE n.id WHEN 1 THEN m.playerLeftWin ELSE NOT m.playerLeftWin END AS Win,
        CASE 
            WHEN n.id = 1 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM matches m
    CROSS JOIN (SELECT 1 AS id UNION ALL SELECT 2) n
),
Aggregated AS (
    SELECT 
        T1, T2, T3,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY T1, T2, T3
)
SELECT 
    (T1 || ', ' || T2 || ', ' || T3) AS Loadout,
    'https://b2.kozow.com/static/' || T1 || '.png' AS T1,
    'https://b2.kozow.com/static/' || T2 || '.png' AS T2,
    'https://b2.kozow.com/static/' || T3 || '.png' AS T3,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
        """
        )
    except:
        pass

    # Hero Loadouts view
    try:
        db.create_view(
            "all_hero_loadouts",
            """
WITH MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM matches
),
Unpivoted AS (
    SELECT 
        CASE n.id WHEN 1 THEN m.lHero ELSE m.rHero END AS Hero,
        CASE n.id WHEN 1 THEN m.lt1 ELSE m.rt1 END AS T1,
        CASE n.id WHEN 1 THEN m.lt2 ELSE m.rt2 END AS T2,
        CASE n.id WHEN 1 THEN m.lt3 ELSE m.rt3 END AS T3,
        CASE n.id WHEN 1 THEN m.playerLeftWin ELSE NOT m.playerLeftWin END AS Win,
        CASE 
            WHEN n.id = 1 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM matches m
    CROSS JOIN (SELECT 1 AS id UNION ALL SELECT 2) n
),
Aggregated AS (
    SELECT 
        Hero, T1, T2, T3,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY Hero, T1, T2, T3
)
SELECT 
    Hero,
    (T1 || ', ' || T2 || ', ' || T3) AS Loadout,
    'https://b2.kozow.com/static/' || Hero || '.png' AS H,
    'https://b2.kozow.com/static/' || T1 || '.png'   AS T1,
    'https://b2.kozow.com/static/' || T2 || '.png'   AS T2,
    'https://b2.kozow.com/static/' || T3 || '.png'   AS T3,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
            """
        )
    except:
        pass

    # Maps view (Unchanged, Maps don't have personal WPA)
    try:
        db.create_view(
            "all_maps",
            """
WITH elite_maps AS (
    SELECT map, duration, endRound
    FROM matches
    WHERE map NOT IN ('bloontonium_mines', 'docks', 'in_the_wall', 'island_base', 'thin_ice')
)
SELECT map AS Map,
       Games,
       REPLACE((CASE
                    WHEN CAST(FLOOR(avg_duration / 60) AS INTEGER) < 10
                        THEN '0' || CAST(FLOOR(avg_duration / 60) AS TEXT)
                    ELSE CAST(FLOOR(avg_duration / 60) AS TEXT)
           END) || ':' ||
               (CASE
                    WHEN CAST(FLOOR(avg_duration % 60) AS INTEGER) < 10
                        THEN '0' || CAST(FLOOR(avg_duration % 60) AS TEXT)
                    ELSE CAST(FLOOR(avg_duration % 60) AS TEXT)
                   END), '.0', '')                                 AS[Average Duration],
       ROUND(avg_end_round, 2)                                     AS [Average End Round],
       ROUND(avg_duration / avg_end_round, 2)                      AS [Seconds per Round]
FROM (SELECT map,
             statistics_median(duration)     AS avg_duration,
             AVG(endRound) + 1               AS avg_end_round,
             COUNT(*)                        AS Games
      FROM elite_maps
      GROUP BY map)
        """
        )
    except:
        pass


def create_map_hero_stats_view(db, map_name):
    view_name = f"{map_name.lower()}_heroes"
    try:
        sql = f"""
WITH {map_name} AS
    (SELECT *
    FROM matches
    WHERE map = '{map_name}'),
MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM {map_name}
),
Unpivoted AS (
    SELECT 
        CASE n.id 
            WHEN 1 THEN m.lHero 
            ELSE m.rHero 
        END AS Hero,
        CASE 
            WHEN n.id = 1 THEN m.playerLeftWin 
            ELSE NOT m.playerLeftWin 
        END AS Win,
        CASE 
            WHEN n.id = 1 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM {map_name} m
    CROSS JOIN (SELECT 1 AS id UNION ALL SELECT 2) n
),
Aggregated AS (
    SELECT 
        Hero,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY Hero
)
SELECT 
    Hero,
    'https://b2.kozow.com/static/' || Hero || '.png' AS Icon,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
    """
        db.create_view(view_name, sql)
    except:
        pass


def create_map_tower_stats_view(db, map_name):
    view_name = f"{map_name.lower()}_towers"
    try:
        sql = f"""
WITH {map_name} AS
    (SELECT *
    FROM matches
    WHERE map = '{map_name}'),
MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM {map_name}
),
Unpivoted AS (
    SELECT 
        CASE n.id
            WHEN 1 THEN m.lt1 WHEN 2 THEN m.lt2 WHEN 3 THEN m.lt3
            WHEN 4 THEN m.rt1 WHEN 5 THEN m.rt2 WHEN 6 THEN m.rt3
        END AS Tower,
        CASE 
            WHEN n.id <= 3 THEN m.playerLeftWin 
            ELSE NOT m.playerLeftWin 
        END AS Win,
        CASE 
            WHEN n.id <= 3 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM {map_name} m
    CROSS JOIN (
        SELECT 1 AS id UNION ALL SELECT 2 UNION ALL SELECT 3 
        UNION ALL SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6
    ) n
),
Aggregated AS (
    SELECT 
        Tower,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY Tower
)
SELECT 
    Tower,
    'https://b2.kozow.com/static/' || Tower || '.png' AS Icon,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
    """
        db.create_view(view_name, sql)
    except:
        pass


def create_map_loadout_stats_view(db, map_name):
    view_name = f"{map_name.lower()}_loadouts"
    try:
        sql = f"""
WITH {map_name} AS
    (SELECT *
    FROM matches
    WHERE map = '{map_name}'),
MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM {map_name}
),
Unpivoted AS (
    SELECT 
        CASE n.id WHEN 1 THEN m.lt1 ELSE m.rt1 END AS T1,
        CASE n.id WHEN 1 THEN m.lt2 ELSE m.rt2 END AS T2,
        CASE n.id WHEN 1 THEN m.lt3 ELSE m.rt3 END AS T3,
        CASE n.id WHEN 1 THEN m.playerLeftWin ELSE NOT m.playerLeftWin END AS Win,
        CASE 
            WHEN n.id = 1 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM {map_name} m
    CROSS JOIN (SELECT 1 AS id UNION ALL SELECT 2) n
),
Aggregated AS (
    SELECT 
        T1, T2, T3,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY T1, T2, T3
)
SELECT 
    (T1 || ', ' || T2 || ', ' || T3) AS Loadout,
    'https://b2.kozow.com/static/' || T1 || '.png' AS T1,
    'https://b2.kozow.com/static/' || T2 || '.png' AS T2,
    'https://b2.kozow.com/static/' || T3 || '.png' AS T3,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10 
ORDER BY WPA_LowerBound_95CI DESC;
    """
        db.create_view(view_name, sql)
    except:
        pass


def create_map_hero_loadout_stats_view(db, map_name):
    view_name = f"{map_name.lower()}_hero_loadouts"
    try:
        sql = f"""
WITH {map_name} AS
    (SELECT *
    FROM matches
    WHERE map = '{map_name}'),
MatchStats AS (
    SELECT COUNT(*) AS TotalMatches FROM {map_name}
),
Unpivoted AS (
    SELECT 
        CASE n.id WHEN 1 THEN m.lHero ELSE m.rHero END AS Hero,
        CASE n.id WHEN 1 THEN m.lt1 ELSE m.rt1 END AS T1,
        CASE n.id WHEN 1 THEN m.lt2 ELSE m.rt2 END AS T2,
        CASE n.id WHEN 1 THEN m.lt3 ELSE m.rt3 END AS T3,
        CASE n.id WHEN 1 THEN m.playerLeftWin ELSE NOT m.playerLeftWin END AS Win,
        CASE 
            WHEN n.id = 1 THEN COALESCE(m.left_wpa, CASE WHEN m.playerLeftWin THEN 0.5 ELSE -0.5 END)
            ELSE COALESCE(m.right_wpa, CASE WHEN NOT m.playerLeftWin THEN 0.5 ELSE -0.5 END)
        END AS WPA
    FROM {map_name} m
    CROSS JOIN (SELECT 1 AS id UNION ALL SELECT 2) n
),
Aggregated AS (
    SELECT 
        Hero, T1, T2, T3,
        COUNT(*) AS Games,
        SUM(Win) AS Wins,
        SUM(NOT Win) AS Losses,
        AVG(WPA) AS AvgWPA,
        AVG(WPA * WPA) AS AvgWPASq
    FROM Unpivoted
    GROUP BY Hero, T1, T2, T3
)
SELECT 
    Hero,
    (T1 || ', ' || T2 || ', ' || T3) AS Loadout,
    'https://b2.kozow.com/static/' || Hero || '.png' AS H,
    'https://b2.kozow.com/static/' || T1 || '.png'   AS T1,
    'https://b2.kozow.com/static/' || T2 || '.png'   AS T2,
    'https://b2.kozow.com/static/' || T3 || '.png'   AS T3,
    Games,
    ROUND(AvgWPA * 100, 2) AS [Win Probability Added],
    ROUND((AvgWPA - 1.96 * SQRT(MAX(0, AvgWPASq - AvgWPA * AvgWPA)) / SQRT(Games)) * 100, 2) AS WPA_LowerBound_95CI
FROM Aggregated
CROSS JOIN MatchStats ms
WHERE Wins >= 10 
  AND Losses >= 10
ORDER BY WPA_LowerBound_95CI DESC;
    """
        db.create_view(view_name, sql)
    except Exception as e:
        print(e)
        pass


def create_map_views(db_path, maps):
    db = sqlite_utils.Database(db_path)
    for map_name in maps:
        create_map_hero_stats_view(db, map_name)
        create_map_tower_stats_view(db, map_name)
        create_map_loadout_stats_view(db, map_name)
        create_map_hero_loadout_stats_view(db, map_name)


def remove_all_views(db_path: str):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name NOT LIKE 'sqlite_%';")
        views = cursor.fetchall()
        if not views:
            return
        for view_name in views:
            name = view_name[0]
            cursor.execute(f"DROP VIEW IF EXISTS {name};")
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def load_maps_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    excluded_maps = "('bloontonium_mines', 'docks', 'in_the_wall', 'island_base', 'thin_ice')"
    try:
        cursor.execute(f"SELECT DISTINCT map FROM matches WHERE map NOT IN {excluded_maps}")
        maps = [row[0] for row in cursor.fetchall()]
        return maps
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def apply_views(db_path, map_list=None):
    if not os.path.exists(db_path):
        return
    print(f"Applying views to: {db_path}")
    global_views(db_path)
    if map_list is None:
        map_list = load_maps_from_db(db_path)
    if map_list:
        create_map_views(db_path, map_list)


DB_FILE_PATTERN = '*_matches.db'
if __name__ == "__main__":
    db_files = glob.glob(DB_FILE_PATTERN)
    if not db_files:
        print(f"No database files found matching the pattern '{DB_FILE_PATTERN}'.")
    else:
        for db_file in db_files:
            remove_all_views(db_file)
            apply_views(db_file)
        print("\nAll databases processed successfully!")