import sqlite3

from main import get_live_hom_id


def sort_towers_in_db(hom_id):
    """Sorts the tower columns (lt1, lt2, lt3 and rt1, rt2, rt3) in the matches table."""

    conn = sqlite3.connect(f'{hom_id}_matches.db')
    cursor = conn.cursor()

    # Fetch all rows from the matches table
    cursor.execute("SELECT match_id, lt1, lt2, lt3, rt1, rt2, rt3 FROM matches")
    rows = cursor.fetchall()

    for row in rows:
        match_id, lt1, lt2, lt3, rt1, rt2, rt3 = row

        # Sort the left towers
        left_towers = sorted([lt1, lt2, lt3], key=lambda x: str(x))

        # Sort the right towers
        right_towers = sorted([rt1, rt2, rt3], key=lambda x: str(x))

        # Update the row with the sorted tower values
        cursor.execute(
            "UPDATE matches SET lt1 = ?, lt2 = ?, lt3 = ?, rt1 = ?, rt2 = ?, rt3 = ? WHERE match_id = ?",
            (left_towers[0], left_towers[1], left_towers[2], right_towers[0], right_towers[1], right_towers[2], match_id)
        )
    # Commit and close
    conn.commit()
    conn.close()
    print("Towers sorted in the database.")


if __name__ == '__main__':
    # Replace 'your_hom_id' with the actual hom_id
    hom_id = 's24+'
    sort_towers_in_db(hom_id)
    hom_id = get_live_hom_id()
    sort_towers_in_db(hom_id)