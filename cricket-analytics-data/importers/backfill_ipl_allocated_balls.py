import os
import csv
import mysql.connector
from pathlib import Path


BASE_DIR = Path(r"D:\CricketAnalytics\cricket-analytics-data")

CSV_PATH = (
    BASE_DIR
    / "processed"
    / "ipl"
    / "match_team_stats.csv"
)


DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
    "database": "cricket_analytics",
}


def safe_int(value):
    if value is None:
        return 0

    return int(value)


def main():

    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL ALLOCATED BALLS DATABASE BACKFILL")
    print("=" * 80)

    print()
    print(f"CSV:")
    print(CSV_PATH)

    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"CSV not found: {CSV_PATH}"
        )

    # ------------------------------------------------------------------
    # Load CSV
    # ------------------------------------------------------------------

    rows = []

    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        required = {
            "match_id",
            "team_name",
            "allocated_balls",
        }

        missing = required - set(
            reader.fieldnames or []
        )

        if missing:
            raise RuntimeError(
                f"CSV is missing columns: {missing}"
            )

        for row in reader:
            rows.append(row)

    print()
    print(f"CSV rows loaded: {len(rows)}")

    # ------------------------------------------------------------------
    # Connect to MySQL
    # ------------------------------------------------------------------

    connection = mysql.connector.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
    )

    cursor = connection.cursor()

    try:

        # --------------------------------------------------------------
        # Load match lookup
        # --------------------------------------------------------------

        cursor.execute(
            """
            SELECT id, external_id
            FROM matches
            WHERE external_id IS NOT NULL
            """
        )

        match_map = {
            str(external_id): match_id
            for match_id, external_id
            in cursor.fetchall()
        }

        # --------------------------------------------------------------
        # Load team lookup
        # --------------------------------------------------------------

        cursor.execute(
            """
            SELECT id, name
            FROM teams
            """
        )

        team_map = {
            name: team_id
            for team_id, name
            in cursor.fetchall()
        }

        print(
            f"Matches available in DB: {len(match_map)}"
        )

        print(
            f"Teams available in DB: {len(team_map)}"
        )

        # --------------------------------------------------------------
        # Validate CSV mappings
        # --------------------------------------------------------------

        updates = []
        missing_matches = []
        missing_teams = []
        invalid_values = []

        for row in rows:

            external_match_id = str(
                row["match_id"]
            )

            team_name = row["team_name"]

            allocated_balls = safe_int(
                row["allocated_balls"]
            )

            if external_match_id not in match_map:

                missing_matches.append(
                    external_match_id
                )

                continue

            if team_name not in team_map:

                missing_teams.append(
                    team_name
                )

                continue

            if allocated_balls <= 0:

                invalid_values.append({
                    "match_id": external_match_id,
                    "team": team_name,
                    "allocated_balls": allocated_balls,
                })

                continue

            updates.append(
                (
                    allocated_balls,
                    match_map[external_match_id],
                    team_map[team_name],
                )
            )

        print()
        print("VALIDATION")
        print("-" * 80)

        print(
            f"Rows ready for update: {len(updates)}"
        )

        print(
            f"Missing matches: {len(missing_matches)}"
        )

        print(
            f"Missing teams: {len(missing_teams)}"
        )

        print(
            f"Invalid allocated balls: {len(invalid_values)}"
        )

        # --------------------------------------------------------------
        # Safety validation
        # --------------------------------------------------------------

        if missing_matches:

            print()
            print("Missing match IDs:")

            for value in sorted(
                set(missing_matches)
            ):
                print(value)

        if missing_teams:

            print()
            print("Missing team names:")

            for value in sorted(
                set(missing_teams)
            ):
                print(value)

        if invalid_values:

            print()
            print("Invalid rows:")

            for value in invalid_values[:20]:
                print(value)

        if (
            missing_matches
            or missing_teams
            or invalid_values
            or len(updates) != len(rows)
        ):

            raise RuntimeError(
                "Validation failed. "
                "NO DATABASE CHANGES WERE MADE."
            )

        # --------------------------------------------------------------
        # Check duplicate match/team targets
        # --------------------------------------------------------------

        targets = {
            (match_id, team_id)
            for _, match_id, team_id in updates
        }

        if len(targets) != len(updates):

            raise RuntimeError(
                "Duplicate match/team targets detected. "
                "NO DATABASE CHANGES WERE MADE."
            )

        # --------------------------------------------------------------
        # Begin database update
        # --------------------------------------------------------------

        print()
        print("Updating database...")

        cursor.executemany(
            """
            UPDATE match_team_stats
            SET allocated_balls = %s
            WHERE match_id = %s
              AND team_id = %s
            """,
            updates
        )

        affected_rows = cursor.rowcount

        print(
            f"Database rows reported updated: "
            f"{affected_rows}"
        )

        # --------------------------------------------------------------
        # Verify ONLY IPL rows
        # --------------------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM match_team_stats mts
            JOIN matches m
                ON m.id = mts.match_id
            WHERE m.competition_id = 4
            """
        )

        ipl_db_rows = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM match_team_stats mts
            JOIN matches m
                ON m.id = mts.match_id
            WHERE m.competition_id = 4
              AND mts.allocated_balls = 0
            """
        )

        ipl_zero_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM match_team_stats
            """
        )

        db_total = cursor.fetchone()[0]

        print()
        print("PRE-COMMIT VERIFICATION")
        print("-" * 80)

        print(
            f"Database match-team rows: {db_total}"
        )

        print(
            f"IPL match-team rows: {ipl_db_rows}"
        )

        print(
            f"IPL rows still having allocated_balls = 0: "
            f"{ipl_zero_count}"
        )

        # --------------------------------------------------------------
        # Verify expected IPL row count
        # --------------------------------------------------------------

        if ipl_db_rows != len(rows):

            connection.rollback()

            raise RuntimeError(
                "IPL CSV/DB row count mismatch. "
                "Transaction rolled back."
            )

        # --------------------------------------------------------------
        # Verify no IPL rows remain zero
        # --------------------------------------------------------------

        if ipl_zero_count != 0:

            connection.rollback()

            raise RuntimeError(
                "Some IPL rows still have allocated_balls = 0. "
                "Transaction rolled back."
            )

        # --------------------------------------------------------------
        # Commit
        # --------------------------------------------------------------

        connection.commit()

        print()
        print("=" * 80)
        print("BACKFILL COMPLETE")
        print("=" * 80)

    except Exception:

        connection.rollback()

        raise

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
