import csv
import getpass
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

import mysql.connector

# =============================================================================
# CRICKET ANALYTICS
# IPL CSV -> MYSQL IMPORTER
# =============================================================================
#
# SAFETY
# -------
# DRY_RUN = True  -> analyse only; NO database writes
# DRY_RUN = False -> perform database import
#
# IMPORT_LIMIT = 10   -> pilot import (chronological first 10 matches)
# IMPORT_LIMIT = None -> full 1,243-match IPL import
#
# IMPORTANT
# ---------
# IPL player_match_performance rows contain team_name in the CSV and the
# database now contains nullable team_id on player_match_performance.
# This importer stores the player's ACTUAL IPL team for that match in
# player_match_performance.team_id.
#
# Existing Player.team is NOT changed for an existing player because one
# Player row cannot represent a player's historical franchise changes.
# =============================================================================


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "processed",
    "ipl"
)

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "cricket_analytics",
    "user": "root",
    # Preferred: set CRICKET_DB_PASSWORD in PowerShell.
    # Otherwise the importer securely asks for it.
    "password": os.getenv("DB_PASSWORD"),
}

# FIRST RUN: keep True.
DRY_RUN = False

# FIRST PILOT: 10 chronological matches.
IMPORT_LIMIT = None


FILES = {
    "teams": os.path.join(
        PROCESSED_DIR,
        "teams.csv"
    ),
    "players": os.path.join(
        PROCESSED_DIR,
        "players.csv"
    ),
    "matches": os.path.join(
        PROCESSED_DIR,
        "matches.csv"
    ),
    "match_team_stats": os.path.join(
        PROCESSED_DIR,
        "match_team_stats.csv"
    ),
    "player_match_performance": os.path.join(
        PROCESSED_DIR,
        "player_match_performance.csv"
    ),
    "player_statistics": os.path.join(
        PROCESSED_DIR,
        "player_statistics.csv"
    ),
}


# =============================================================================
# IPL TEAM CODES
# =============================================================================

TEAM_SHORT_NAMES = {
    "Mumbai Indians": "MI",
    "Kolkata Knight Riders": "KKR",
    "Chennai Super Kings": "CSK",
    "Rajasthan Royals": "RR",
    "Royal Challengers Bengaluru": "RCB",
    "Sunrisers Hyderabad": "SRH",
    "Punjab Kings": "PBKS",
    "Delhi Capitals": "DC",
    "Deccan Chargers": "DEC",
    "Gujarat Titans": "GT",
    "Gujarat Lions": "GL",
    "Lucknow Super Giants": "LSG",
    "Pune Warriors": "PWI",
    "Rising Pune Supergiant": "RPS",
    "Kochi Tuskers Kerala": "KTK",
}


# =============================================================================
# HELPERS
# =============================================================================

def fail(message):
    print()
    print("=" * 80)
    print("ERROR")
    print("=" * 80)
    print(message)
    print()
    sys.exit(1)


def load_csv(path):
    if not os.path.exists(path):
        fail(f"CSV file not found:\n{path}")

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def text(value):
    if value is None:
        return None

    value = str(value).strip()
    return value if value else None


def integer(value, default=0):
    if value is None or str(value).strip() == "":
        return default

    try:
        return int(float(value))
    except (TypeError, ValueError):
        fail(f"Invalid integer value: {value}")


def decimal(value, default=0.0):
    if value is None or str(value).strip() == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        fail(f"Invalid decimal value: {value}")


def boolean(value):
    if value is None:
        return False

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y"
    }


def normalize_gender(value):
    value = text(value)

    if not value:
        return "male"

    return value.lower()


def normalize_key(value):
    value = text(value)

    if not value:
        return ""

    return " ".join(value.lower().split())


def team_key(name, gender):
    return (
        normalize_key(name),
        normalize_gender(gender)
    )


def parse_date(value):
    value = text(value)

    if not value:
        fail("A match has no match_date.")

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        fail(f"Invalid match date: {value}")


def season_years(season_name):
    """
    Convert IPL season labels to start/end years.

    Examples:
        2007/08 -> 2007, 2008
        2009/10 -> 2009, 2010
        2020/21 -> 2020, 2021
        2026    -> 2026, 2026
    """
    value = text(season_name)

    if not value:
        fail("Encountered an empty IPL season name.")

    parts = value.split("/")

    try:
        start_year = int(parts[0])
    except ValueError:
        fail(f"Invalid IPL season name: {value}")

    if len(parts) == 1:
        return start_year, start_year

    suffix = parts[1]

    if len(suffix) == 2:
        century = (start_year // 100) * 100
        end_year = century + int(suffix)

        if end_year < start_year:
            end_year += 100

        return start_year, end_year

    try:
        return start_year, int(suffix)
    except ValueError:
        fail(f"Invalid IPL season name: {value}")


# =============================================================================
# CSV LOAD + VALIDATION
# =============================================================================

REQUIRED_COLUMNS = {
    "teams": {
        "team_id",
        "team_name",
        "gender",
    },
    "players": {
        "player_external_id",
        "player_name",
        "gender",
        "team_name",
    },
    "matches": {
        "match_id",
        "match_date",
        "season",
        "gender",
        "match_type",
        "team1",
        "team2",
        "venue",
        "city",
        "toss_winner",
        "toss_decision",
        "winner",
        "match_status",
        "result_type",
        "result_description",
        "super_over_count",
    },
    "match_team_stats": {
        "match_id",
        "team_name",
        "runs",
        "wickets",
        "total_balls",
        "fours",
        "sixes",
        "extras",
        "run_rate",
    },
    "player_match_performance": {
        "match_id",
        "player_external_id",
        "player_name",
        "team_name",
        "batting_runs",
        "balls_faced",
        "fours",
        "sixes",
        "batting_strike_rate",
        "not_out",
        "balls_bowled",
        "runs_conceded",
        "wickets",
        "bowling_economy",
        "maidens",
        "batted",
    },
    "player_statistics": {
        "player_external_id",
        "player_name",
        "team_name",
        "season",
        "matches",
        "batting_innings",
        "runs",
        "balls_faced",
        "highest_score",
        "not_outs",
        "fours",
        "sixes",
        "fifties",
        "centuries",
        "batting_average",
        "strike_rate",
        "bowling_innings",
        "balls_bowled",
        "wickets",
        "runs_conceded",
        "economy",
        "bowling_average",
        "best_bowling_wickets",
        "five_wicket_hauls",
    },
}


def validate_columns(data, name):
    rows = data[name]

    if not rows:
        fail(f"{name}.csv contains no records.")

    actual = set(rows[0].keys())
    missing = REQUIRED_COLUMNS[name] - actual

    if missing:
        fail(
            f"{name}.csv is missing columns:\n"
            + ", ".join(sorted(missing))
        )


def validate_csv_data(data):
    print()
    print("=" * 80)
    print("CSV STRUCTURE VALIDATION")
    print("=" * 80)

    for name in REQUIRED_COLUMNS:
        validate_columns(data, name)

    match_ids = [
        text(row["match_id"])
        for row in data["matches"]
    ]

    if None in match_ids:
        fail("matches.csv contains a row without match_id.")

    if len(match_ids) != len(set(match_ids)):
        fail("matches.csv contains duplicate match_id values.")

    player_ids = [
        text(row["player_external_id"])
        for row in data["players"]
    ]

    if None in player_ids:
        fail("players.csv contains a player without player_external_id.")

    if len(player_ids) != len(set(player_ids)):
        fail("players.csv contains duplicate player_external_id values.")

    player_match_keys = [
        (
            text(row["match_id"]),
            text(row["player_external_id"])
        )
        for row in data["player_match_performance"]
    ]

    if len(player_match_keys) != len(set(player_match_keys)):
        fail(
            "player_match_performance.csv contains duplicate "
            "(match_id, player_external_id) values."
        )

    player_season_keys = [
        (
            text(row["player_external_id"]),
            text(row["season"])
        )
        for row in data["player_statistics"]
    ]

    if len(player_season_keys) != len(set(player_season_keys)):
        fail(
            "player_statistics.csv contains duplicate "
            "(player_external_id, season) values."
        )

    valid_genders = {"male", "female"}

    for row in data["matches"]:
        if text(row["match_type"]).upper() != "T20":
            fail(
                f"Non-T20 record found: "
                f"{row['match_id']} / {row['match_type']}"
            )

        if normalize_gender(row["gender"]) not in valid_genders:
            fail(
                f"Unexpected gender for match {row['match_id']}: "
                f"{row['gender']}"
            )

        parse_date(row["match_date"])
        season_years(row["season"])

    for row in data["player_match_performance"]:
        wickets = integer(row["wickets"])
        if wickets < 0 or wickets > 10:
            fail(
                f"Invalid player wickets: {row['player_name']} / "
                f"{row['match_id']} / {wickets}"
            )

    for row in data["match_team_stats"]:
        if integer(row["runs"]) < 0:
            fail(f"Negative team runs: {row['match_id']}")
        if integer(row["wickets"]) < 0:
            fail(f"Negative team wickets: {row['match_id']}")

    print()
    print("CSV structure and integrity: PASS")


def load_all_csvs():
    print("=" * 80)
    print("IPL CSV -> MYSQL IMPORTER")
    print("=" * 80)

    print()
    print("Processed directory:")
    print(PROCESSED_DIR)

    print()
    print("Loading CSV files...")

    data = {}

    for name, path in FILES.items():
        rows = load_csv(path)
        data[name] = rows

        print(
            f"  {name:<32}"
            f"{len(rows):>10,} records"
        )

    print()
    print("All CSV files loaded successfully.")

    return data


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def connect_database():
    password = DB_CONFIG["password"]

    if not password:
        password = getpass.getpass(
            "Enter MySQL root password: "
        )

    print()
    print("=" * 80)
    print("MYSQL CONNECTION")
    print("=" * 80)

    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=password,
        )
    except mysql.connector.Error as error:
        fail(
            "Could not connect to MySQL.\n\n"
            f"MySQL error: {error}"
        )

    print()
    print("MySQL connection: PASS")
    print(f"Database: {DB_CONFIG['database']}")

    return connection


# =============================================================================
# EXISTING DATABASE STATE
# =============================================================================

def get_existing_teams(cursor):
    cursor.execute(
        """
        SELECT id, name, short_name, country, gender
        FROM teams
        """
    )

    result = {}

    for row in cursor.fetchall():
        result[team_key(row[1], row[4])] = {
            "id": row[0],
            "name": row[1],
            "short_name": row[2],
            "country": row[3],
            "gender": row[4],
        }

    return result


def get_existing_players(cursor):
    cursor.execute(
        """
        SELECT id, external_id, name, role, team_id
        FROM players
        """
    )

    result = {}

    for row in cursor.fetchall():
        if row[1]:
            result[str(row[1])] = {
                "id": row[0],
                "external_id": row[1],
                "name": row[2],
                "role": row[3],
                "team_id": row[4],
            }

    return result


def get_existing_competitions(cursor):
    cursor.execute(
        """
        SELECT id, name, type, format
        FROM competitions
        """
    )

    result = {}

    for row in cursor.fetchall():
        result[normalize_key(row[1])] = {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "format": row[3],
        }

    return result


def get_existing_seasons(cursor):
    cursor.execute(
        """
        SELECT id, name, start_year, end_year, competition_id
        FROM seasons
        """
    )

    result = {}

    for row in cursor.fetchall():
        result[(row[4], normalize_key(row[1]))] = {
            "id": row[0],
            "name": row[1],
            "start_year": row[2],
            "end_year": row[3],
            "competition_id": row[4],
        }

    return result


def get_existing_venues(cursor):
    cursor.execute(
        """
        SELECT id, name, city, country, capacity
        FROM venues
        """
    )

    result = {}

    for row in cursor.fetchall():
        result[normalize_key(row[1])] = {
            "id": row[0],
            "name": row[1],
            "city": row[2],
            "country": row[3],
            "capacity": row[4],
        }

    return result


def get_existing_matches(cursor):
    cursor.execute(
        """
        SELECT id, external_id, stage
        FROM matches
        WHERE external_id IS NOT NULL
        """
    )

    return {
        str(row[1]): {"id": row[0], "stage": row[2]}
        for row in cursor.fetchall()
    }


def load_database_state(connection):
    cursor = connection.cursor()

    try:
        state = {
            "teams": get_existing_teams(cursor),
            "players": get_existing_players(cursor),
            "competitions": get_existing_competitions(cursor),
            "seasons": get_existing_seasons(cursor),
            "venues": get_existing_venues(cursor),
            "matches": get_existing_matches(cursor),
        }
    finally:
        cursor.close()

    print()
    print("=" * 80)
    print("EXISTING DATABASE STATE")
    print("=" * 80)
    print(f"\nExisting teams:             {len(state['teams']):>8,}")
    print(f"Existing players:           {len(state['players']):>8,}")
    print(f"Existing competitions:      {len(state['competitions']):>8,}")
    print(f"Existing seasons:           {len(state['seasons']):>8,}")
    print(f"Existing venues:            {len(state['venues']):>8,}")
    print(f"Existing imported matches:  {len(state['matches']):>8,}")

    return state


# =============================================================================
# MATCH SELECTION / DEPENDENCY FILTERING
# =============================================================================

def select_matches(data):
    matches = sorted(
        data["matches"],
        key=lambda row: (
            text(row["match_date"]) or "",
            text(row["match_id"]) or ""
        )
    )

    if IMPORT_LIMIT is None:
        return matches

    return matches[:IMPORT_LIMIT]


def filter_dependent_data(data, selected_matches):
    selected_ids = {
        str(row["match_id"])
        for row in selected_matches
    }

    filtered = dict(data)
    filtered["matches"] = selected_matches

    filtered["match_team_stats"] = [
        row for row in data["match_team_stats"]
        if str(row["match_id"]) in selected_ids
    ]

    filtered["player_match_performance"] = [
        row for row in data["player_match_performance"]
        if str(row["match_id"]) in selected_ids
    ]

    selected_player_ids = {
        text(row["player_external_id"])
        for row in filtered["player_match_performance"]
        if text(row["player_external_id"])
    }

    filtered["players"] = [
        row for row in data["players"]
        if text(row["player_external_id"]) in selected_player_ids
    ]

    selected_team_keys = set()

    for row in selected_matches:
        gender = normalize_gender(row["gender"])
        selected_team_keys.add(team_key(row["team1"], gender))
        selected_team_keys.add(team_key(row["team2"], gender))

    for row in filtered["match_team_stats"]:
        selected_team_keys.add(
            team_key(row["team_name"], "male")
        )

    for row in filtered["player_match_performance"]:
        selected_team_keys.add(
            team_key(row["team_name"], "male")
        )

    filtered["teams"] = [
        row for row in data["teams"]
        if team_key(
            row["team_name"],
            row["gender"]
        ) in selected_team_keys
    ]

    return filtered


# =============================================================================
# TEAM MAPPING
# =============================================================================

def generate_short_name(team_name, used_codes):
    preferred = TEAM_SHORT_NAMES.get(team_name)

    if preferred:
        code = preferred
    else:
        letters = [
            ch.upper()
            for ch in team_name
            if ch.isalnum()
        ]
        code = "".join(letters[:3])

        if len(code) < 3:
            code = (code + "XXX")[:3]

    original = code
    counter = 1

    while code in used_codes:
        suffix = str(counter)
        prefix_length = max(1, 3 - len(suffix))
        code = original[:prefix_length] + suffix
        counter += 1

        if len(code) > 3:
            fail(f"Could not generate team short name for {team_name}")

    used_codes.add(code)
    return code


def prepare_team_mapping(data, database_state):
    existing = database_state["teams"]
    mapping = {}

    used_codes = {
        record["short_name"]
        for record in existing.values()
        if record.get("short_name")
    }

    unique_teams = {}

    for row in data["teams"]:
        name = text(row["team_name"])
        gender = normalize_gender(row["gender"])

        if not name:
            continue

        key = team_key(name, gender)

        unique_teams[key] = {
            "name": name,
            "gender": gender,
        }

    existing_count = 0
    new_count = 0

    for key, info in sorted(unique_teams.items()):
        if key in existing:
            mapping[key] = dict(existing[key])
            existing_count += 1
            continue

        short_name = generate_short_name(
            info["name"],
            used_codes
        )

        mapping[key] = {
            "id": None,
            "name": info["name"],
            "short_name": short_name,
            "country": info["name"],
            "gender": info["gender"],
        }
        new_count += 1

    return mapping, existing_count, new_count


def resolve_team(team_mapping, name, gender="male"):
    key = team_key(name, gender)

    if key not in team_mapping:
        fail(
            "Could not resolve team:\n"
            f"Name: {name}\n"
            f"Gender: {gender}"
        )

    team = team_mapping[key]

    if team["id"] is None:
        fail(
            "Team has no database ID:\n"
            f"{name} / {gender}"
        )

    return team


def insert_teams(connection, team_mapping):
    cursor = connection.cursor()
    created = 0

    try:
        for team in team_mapping.values():
            if team["id"] is not None:
                continue

            cursor.execute(
                """
                INSERT INTO teams
                    (name, short_name, country, gender)
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    team["name"],
                    team["short_name"],
                    team["country"],
                    team["gender"],
                )
            )

            team["id"] = cursor.lastrowid
            created += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return created


# =============================================================================
# PLAYER MAPPING
# =============================================================================

def prepare_player_mapping(data, database_state, team_mapping):
    existing = database_state["players"]
    mapping = {}

    # Count match appearances by team so that new IPL-only players receive a
    # sensible default/current team. Historical match-team truth is stored in
    # player_match_performance.team_id.
    player_team_counts = defaultdict(Counter)

    for row in data["player_match_performance"]:
        external_id = text(row["player_external_id"])
        team_name = text(row["team_name"])

        if external_id and team_name:
            player_team_counts[external_id][
                team_key(team_name, "male")
            ] += 1

    existing_count = 0
    new_count = 0

    for row in data["players"]:
        external_id = text(row["player_external_id"])

        if not external_id:
            fail(
                f"Player has no external ID: {row['player_name']}"
            )

        if external_id in mapping:
            continue

        if external_id in existing:
            # CRITICAL: don't overwrite Player.team for existing players.
            # International players may have an international team here, while
            # their IPL franchise is stored per match below.
            mapping[external_id] = dict(existing[external_id])
            mapping[external_id]["is_existing"] = True
            existing_count += 1
            continue

        name = text(row["player_name"])
        preferred_team_key = None

        if external_id in player_team_counts:
            preferred_team_key = (
                player_team_counts[external_id]
                .most_common(1)[0][0]
            )

        team_id = None

        if preferred_team_key in team_mapping:
            team_id = team_mapping[preferred_team_key]["id"]

        mapping[external_id] = {
            "id": None,
            "external_id": external_id,
            "name": name,
            "role": "OTHER",
            "batting_style": None,
            "bowling_style": None,
            "team_id": team_id,
            "team_key": preferred_team_key,
            "is_existing": False,
        }

        new_count += 1

    return mapping, existing_count, new_count


def insert_players(connection, player_mapping):
    cursor = connection.cursor()
    created = 0

    try:
        for player in player_mapping.values():
            if player["id"] is not None:
                continue

            cursor.execute(
                """
                INSERT INTO players
                    (
                        name,
                        external_id,
                        role,
                        batting_style,
                        bowling_style,
                        team_id
                    )
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                (
                    player["name"],
                    player["external_id"],
                    player["role"],
                    player["batting_style"],
                    player["bowling_style"],
                    player["team_id"],
                )
            )

            player["id"] = cursor.lastrowid
            created += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return created


# =============================================================================
# COMPETITION
# =============================================================================

def prepare_competition(database_state):
    competitions = database_state["competitions"]

    # Prefer the existing seeded competition.
    for key in (
        "indian premier league",
        "ipl",
    ):
        if key in competitions:
            return dict(competitions[key])

    return {
        "id": None,
        "name": "Indian Premier League",
        "type": "IPL",
        "format": "T20",
    }


def ensure_competition(connection, competition):
    if competition["id"] is not None:
        return competition

    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO competitions
                (name, type, format)
            VALUES
                (%s, %s, %s)
            """,
            (
                competition["name"],
                competition["type"],
                competition["format"],
            )
        )

        competition["id"] = cursor.lastrowid
        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return competition


# =============================================================================
# SEASONS
# =============================================================================

def ensure_seasons(connection, competition, data, database_state):
    seasons = dict(database_state["seasons"])
    competition_id = competition["id"]

    season_names = sorted({
        text(row["season"])
        for row in data["matches"]
        if text(row["season"])
    })

    created = 0

    print()
    print("=" * 80)
    print("IPL SEASON SETUP")
    print("=" * 80)

    for season_name in season_names:
        key = (
            competition_id,
            normalize_key(season_name)
        )

        if key in seasons:
            continue

        start_year, end_year = season_years(season_name)

        cursor = connection.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO seasons
                    (
                        name,
                        start_year,
                        end_year,
                        competition_id
                    )
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    season_name,
                    start_year,
                    end_year,
                    competition_id,
                )
            )

            season_id = cursor.lastrowid
            connection.commit()

            seasons[key] = {
                "id": season_id,
                "name": season_name,
                "start_year": start_year,
                "end_year": end_year,
                "competition_id": competition_id,
            }

            created += 1
            print(f"  Created IPL season: {season_name}")

        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()

    print(f"Seasons created: {created}")

    return seasons, created


# =============================================================================
# VENUES
# =============================================================================

def prepare_venue_mapping(data, database_state):
    existing = database_state["venues"]
    mapping = {}

    for row in data["matches"]:
        name = text(row["venue"])

        if not name:
            fail(
                f"Match {row['match_id']} has no venue."
            )

        key = normalize_key(name)

        if key in mapping:
            continue

        if key in existing:
            mapping[key] = dict(existing[key])
        else:
            mapping[key] = {
                "id": None,
                "name": name,
                "city": text(row["city"]),
                "country": None,
                "capacity": None,
            }

    return mapping


def insert_venues(connection, venue_mapping):
    cursor = connection.cursor()
    created = 0

    try:
        for venue in venue_mapping.values():
            if venue["id"] is not None:
                continue

            cursor.execute(
                """
                INSERT INTO venues
                    (name, city, country, capacity)
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    venue["name"],
                    venue["city"],
                    venue["country"],
                    venue["capacity"],
                )
            )

            venue["id"] = cursor.lastrowid
            created += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return created


# =============================================================================
# MATCHES
# =============================================================================

def normalize_match_status(result_type, winner_name):
    value = (text(result_type) or "").lower()

    if "no result" in value or value in {"no_result", "no-result"}:
        return "NO_RESULT"

    if "tie" in value or value == "tied":
        return "COMPLETED"

    if "draw" in value:
        return "DRAW"

    if winner_name:
        return "COMPLETED"

    if value:
        return value.upper().replace(" ", "_").replace("-", "_")

    return "UNKNOWN"


def insert_matches(
    connection,
    data,
    team_mapping,
    venue_mapping,
    seasons,
    competition,
    database_state,
):
    cursor = connection.cursor()

    existing_matches = database_state["matches"]
    match_mapping = {}

    imported = 0
    reused = 0

    try:
        for row in data["matches"]:
            external_id = text(row["match_id"])

            if not external_id:
                fail("Match has no match_id.")

            if external_id in existing_matches:
                existing_match = existing_matches[external_id]
                match_mapping[external_id] = existing_match["id"]

                # The stage column was added after the original IPL import.
                # Backfill it for already-imported matches so the existing
                # 1,243 matches become stage-aware without re-inserting them.
                stage = text(row["stage"]) or "League"
                if existing_match.get("stage") != stage:
                    cursor.execute(
                        """
                        UPDATE matches
                        SET stage = %s
                        WHERE id = %s
                        """,
                        (
                            stage,
                            existing_match["id"],
                        )
                    )

                reused += 1
                continue

            gender = normalize_gender(row["gender"])

            team1 = resolve_team(
                team_mapping,
                row["team1"],
                gender
            )

            team2 = resolve_team(
                team_mapping,
                row["team2"],
                gender
            )

            venue = venue_mapping.get(
                normalize_key(row["venue"])
            )

            if not venue or venue["id"] is None:
                fail(
                    f"Could not resolve venue: {row['venue']}"
                )

            season_name = text(row["season"])
            season_key = (
                competition["id"],
                normalize_key(season_name)
            )

            if season_key not in seasons:
                fail(
                    f"No IPL season found for: {season_name}"
                )

            season = seasons[season_key]

            toss_winner = None
            toss_name = text(row["toss_winner"])

            if toss_name:
                toss_key = team_key(toss_name, gender)
                if toss_key in team_mapping:
                    toss_winner = team_mapping[toss_key]
                else:
                    print(
                        f"  Warning: unresolved toss winner "
                        f"'{toss_name}' in match {external_id}; NULL."
                    )

            winner = None
            winner_name = text(row["winner"])

            if winner_name:
                winner_key = team_key(winner_name, gender)

                if winner_key in team_mapping:
                    winner = team_mapping[winner_key]
                else:
                    print(
                        f"  Warning: unresolved winner "
                        f"'{winner_name}' in match {external_id}; NULL."
                    )

            match_status = normalize_match_status(
                row["result_type"],
                winner_name
            )

            cursor.execute(
                """
                INSERT INTO matches
                    (
                        external_id,
                        match_date,
                        match_status,
                        toss_decision,
                        result_description,
                        stage,
                        competition_id,
                        season_id,
                        venue_id,
                        team1_id,
                        team2_id,
                        toss_winner_team_id,
                        winner_team_id
                    )
                VALUES
                    (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                """,
                (
                    external_id,
                    parse_date(row["match_date"]),
                    match_status,
                    text(row["toss_decision"]),
                    text(row["result_description"]),
                    text(row["stage"]) or "League",
                    competition["id"],
                    season["id"],
                    venue["id"],
                    team1["id"],
                    team2["id"],
                    toss_winner["id"] if toss_winner else None,
                    winner["id"] if winner else None,
                )
            )

            match_mapping[external_id] = cursor.lastrowid
            imported += 1

            if imported % 100 == 0:
                print(f"  Matches imported: {imported:,}")

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return match_mapping, imported, reused


# =============================================================================
# EXISTING CHILD RECORD LOOKUPS
# =============================================================================

def get_existing_match_team_stats(cursor):
    cursor.execute(
        """
        SELECT match_id, team_id
        FROM match_team_stats
        """
    )

    return {
        (row[0], row[1])
        for row in cursor.fetchall()
    }


def get_existing_player_match_performance(cursor):
    cursor.execute(
        """
        SELECT match_id, player_id
        FROM player_match_performance
        """
    )

    return {
        (row[0], row[1])
        for row in cursor.fetchall()
    }


def get_existing_player_statistics(cursor):
    cursor.execute(
        """
        SELECT player_id, competition_id, season_id, scope
        FROM player_statistics
        """
    )

    return {
        (row[0], row[1], row[2], row[3])
        for row in cursor.fetchall()
    }


# =============================================================================
# MATCH TEAM STATS
# =============================================================================

def insert_match_team_stats(
    connection,
    data,
    match_mapping,
    team_mapping,
):
    cursor = connection.cursor()
    existing = get_existing_match_team_stats(cursor)

    inserted = 0
    skipped = 0

    try:
        for row in data["match_team_stats"]:
            external_match_id = text(row["match_id"])

            if external_match_id not in match_mapping:
                continue

            db_match_id = match_mapping[external_match_id]
            team = resolve_team(
                team_mapping,
                row["team_name"],
                "male"
            )

            unique_key = (
                db_match_id,
                team["id"]
            )

            if unique_key in existing:
                skipped += 1
                continue

            cursor.execute(
                """
                INSERT INTO match_team_stats
                    (
                        match_id,
                        team_id,
                        runs,
                        wickets,
                        total_balls,
                        fours,
                        sixes,
                        extras,
                        run_rate
                    )
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    db_match_id,
                    team["id"],
                    integer(row["runs"]),
                    integer(row["wickets"]),
                    integer(row["total_balls"]),
                    integer(row["fours"]),
                    integer(row["sixes"]),
                    integer(row["extras"]),
                    decimal(row["run_rate"]),
                )
            )

            existing.add(unique_key)
            inserted += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return inserted, skipped


# =============================================================================
# PLAYER MATCH PERFORMANCE
# =============================================================================
#
# IMPORTANT:
# The PlayerMatchPerformance entity/table now has nullable team_id.
# We insert it here for every IPL performance row.
# batted is intentionally NOT inserted because the database entity/table does
# not currently have a batted column.
# =============================================================================

def insert_player_match_performance(
    connection,
    data,
    match_mapping,
    player_mapping,
    team_mapping,
):
    cursor = connection.cursor()
    existing = get_existing_player_match_performance(cursor)

    inserted = 0
    skipped = 0

    try:
        for row in data["player_match_performance"]:
            external_match_id = text(row["match_id"])
            external_player_id = text(row["player_external_id"])

            if external_match_id not in match_mapping:
                continue

            if external_player_id not in player_mapping:
                fail(
                    "Player performance references unknown player:\n"
                    f"{external_player_id}"
                )

            player = player_mapping[external_player_id]

            if player["id"] is None:
                fail(
                    "Player has no database ID:\n"
                    f"{external_player_id}"
                )

            team = resolve_team(
                team_mapping,
                row["team_name"],
                "male"
            )

            db_match_id = match_mapping[external_match_id]

            unique_key = (
                db_match_id,
                player["id"]
            )

            if unique_key in existing:
                skipped += 1
                continue

            cursor.execute(
                """
                INSERT INTO player_match_performance
                    (
                        match_id,
                        player_id,
                        team_id,
                        batting_runs,
                        balls_faced,
                        fours,
                        sixes,
                        batting_strike_rate,
                        not_out,
                        balls_bowled,
                        runs_conceded,
                        wickets,
                        bowling_economy,
                        maidens
                    )
                VALUES
                    (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """,
                (
                    db_match_id,
                    player["id"],
                    team["id"],
                    integer(row["batting_runs"]),
                    integer(row["balls_faced"]),
                    integer(row["fours"]),
                    integer(row["sixes"]),
                    decimal(row["batting_strike_rate"]),
                    boolean(row["not_out"]),
                    integer(row["balls_bowled"]),
                    integer(row["runs_conceded"]),
                    integer(row["wickets"]),
                    decimal(row["bowling_economy"]),
                    integer(row["maidens"]),
                )
            )

            existing.add(unique_key)
            inserted += 1

            if inserted % 1000 == 0:
                print(
                    f"  Player performances: {inserted:,}"
                )

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return inserted, skipped


# =============================================================================
# PLAYER SEASON STATISTICS
# =============================================================================
#
# The IPL processor produces season-level rows, so these are stored with
# scope='SEASON'. This is different from the ODI importer, whose career CSV
# was stored with scope='CAREER'.
# =============================================================================

def insert_player_statistics(
    connection,
    data,
    player_mapping,
    competition,
    seasons,
):
    cursor = connection.cursor()
    existing = get_existing_player_statistics(cursor)

    inserted = 0
    skipped = 0

    try:
        for row in data["player_statistics"]:
            external_id = text(row["player_external_id"])

            if external_id not in player_mapping:
                fail(
                    "Player statistics references unknown player:\n"
                    f"{external_id}"
                )

            player = player_mapping[external_id]

            if player["id"] is None:
                fail(
                    "Player statistics references player without ID:\n"
                    f"{external_id}"
                )

            season_name = text(row["season"])
            season_key = (
                competition["id"],
                normalize_key(season_name)
            )

            if season_key not in seasons:
                fail(
                    f"No IPL season found for statistics: {season_name}"
                )

            season = seasons[season_key]
            scope = "SEASON"

            unique_key = (
                player["id"],
                competition["id"],
                season["id"],
                scope,
            )

            if unique_key in existing:
                skipped += 1
                continue

            cursor.execute(
                """
                INSERT INTO player_statistics
                    (
                        player_id,
                        competition_id,
                        season_id,
                        scope,
                        matches,
                        batting_innings,
                        runs,
                        balls_faced,
                        highest_score,
                        not_outs,
                        fours,
                        sixes,
                        fifties,
                        centuries,
                        batting_average,
                        strike_rate,
                        bowling_innings,
                        balls_bowled,
                        wickets,
                        runs_conceded,
                        economy,
                        bowling_average,
                        best_bowling_wickets,
                        five_wicket_hauls
                    )
                VALUES
                    (
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s
                    )
                """,
                (
                    player["id"],
                    competition["id"],
                    season["id"],
                    scope,
                    integer(row["matches"]),
                    integer(row["batting_innings"]),
                    integer(row["runs"]),
                    integer(row["balls_faced"]),
                    integer(row["highest_score"]),
                    integer(row["not_outs"]),
                    integer(row["fours"]),
                    integer(row["sixes"]),
                    integer(row["fifties"]),
                    integer(row["centuries"]),
                    decimal(row["batting_average"]),
                    decimal(row["strike_rate"]),
                    integer(row["bowling_innings"]),
                    integer(row["balls_bowled"]),
                    integer(row["wickets"]),
                    integer(row["runs_conceded"]),
                    decimal(row["economy"]),
                    decimal(row["bowling_average"]),
                    integer(row["best_bowling_wickets"]),
                    integer(row["five_wicket_hauls"]),
                )
            )

            existing.add(unique_key)
            inserted += 1

        connection.commit()

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()

    return inserted, skipped


# =============================================================================
# DRY RUN ANALYSIS
# =============================================================================

def analyse(data, database_state):
    selected_matches = select_matches(data)
    selected_data = filter_dependent_data(
        data,
        selected_matches
    )

    team_mapping, existing_teams, new_teams = prepare_team_mapping(
        selected_data,
        database_state
    )

    player_mapping, existing_players, new_players = prepare_player_mapping(
        selected_data,
        database_state,
        team_mapping
    )

    competition = prepare_competition(database_state)

    csv_venues = {
        normalize_key(row["venue"])
        for row in selected_data["matches"]
        if text(row["venue"])
    }

    existing_venue_count = sum(
        1
        for venue in csv_venues
        if venue in database_state["venues"]
    )

    new_venue_count = (
        len(csv_venues) - existing_venue_count
    )

    selected_match_ids = {
        text(row["match_id"])
        for row in selected_matches
    }

    already_imported = sum(
        1
        for match_id in selected_match_ids
        if match_id in database_state["matches"]
    )

    new_matches = (
        len(selected_match_ids) - already_imported
    )

    print()
    print("=" * 80)
    print("DRY-RUN ANALYSIS")
    print("=" * 80)

    print()
    print("IMPORT SCOPE")
    print(f"  Selected matches:          {len(selected_matches):>8,}")
    print(f"  Match-team stats:          {len(selected_data['match_team_stats']):>8,}")
    print(f"  Player-match performances: {len(selected_data['player_match_performance']):>8,}")
    print(f"  Player statistics:         {len(selected_data['player_statistics']):>8,}")

    print()
    print("TEAMS")
    print(f"  Team identities:           {len(team_mapping):>8,}")
    print(f"  Existing teams:            {existing_teams:>8,}")
    print(f"  New teams:                 {new_teams:>8,}")

    print()
    print("PLAYERS")
    print(f"  Selected players:          {len(player_mapping):>8,}")
    print(f"  Existing players:          {existing_players:>8,}")
    print(f"  New players:               {new_players:>8,}")

    print()
    print("VENUES")
    print(f"  Selected venues:           {len(csv_venues):>8,}")
    print(f"  Existing venues:           {existing_venue_count:>8,}")
    print(f"  New venues:                {new_venue_count:>8,}")

    print()
    print("MATCHES")
    print(f"  Selected matches:          {len(selected_match_ids):>8,}")
    print(f"  Already imported:          {already_imported:>8,}")
    print(f"  New matches:               {new_matches:>8,}")

    print()
    print("SEASONS")
    season_counts = Counter(
        text(row["season"])
        for row in selected_matches
    )

    for season_name in sorted(season_counts):
        print(
            f"  {season_name:<25}"
            f"{season_counts[season_name]:>8,} matches"
        )

    print()
    print("COMPETITION")
    if competition["id"]:
        print(f"  {competition['name']}:       EXISTS")
        print(f"  Database ID:               {competition['id']}")
    else:
        print(
            f"  {competition['name']}:       WILL BE CREATED"
        )

    print()
    print("PLAYER TEAM HANDLING")
    print("  Existing Player.team:      NOT CHANGED")
    print("  IPL match team:            STORED IN player_match_performance.team_id")

    print()
    print("PLAYER STATISTICS")
    if IMPORT_LIMIT is None:
        print("  Scope:                     SEASON")
        print("  Statistics:                WILL BE IMPORTED")
    else:
        print("  Statistics:                SKIPPED FOR PILOT")

    print()
    print("=" * 80)
    print("DRY-RUN RESULT")
    print("=" * 80)
    print()
    print("NO DATABASE CHANGES WERE MADE.")


# =============================================================================
# IMPORT
# =============================================================================

def print_import_summary(
    team_created,
    player_created,
    venue_created,
    season_created,
    match_imported,
    match_reused,
    match_team_inserted,
    match_team_skipped,
    performance_inserted,
    performance_skipped,
    statistics_inserted,
    statistics_skipped,
):
    print()
    print("=" * 80)
    print("IPL IMPORT RESULT")
    print("=" * 80)

    print()
    print("BASE ENTITIES")
    print(f"  Teams created:             {team_created:>8,}")
    print(f"  Players created:           {player_created:>8,}")
    print(f"  Venues created:            {venue_created:>8,}")
    print(f"  Seasons created:           {season_created:>8,}")

    print()
    print("MATCHES")
    print(f"  Matches imported:          {match_imported:>8,}")
    print(f"  Existing matches reused:   {match_reused:>8,}")

    print()
    print("MATCH TEAM STATS")
    print(f"  Inserted:                  {match_team_inserted:>8,}")
    print(f"  Already existed:           {match_team_skipped:>8,}")

    print()
    print("PLAYER MATCH PERFORMANCE")
    print(f"  Inserted:                  {performance_inserted:>8,}")
    print(f"  Already existed:           {performance_skipped:>8,}")

    print()
    print("PLAYER SEASON STATISTICS")
    print(f"  Inserted:                  {statistics_inserted:>8,}")
    print(f"  Already existed:           {statistics_skipped:>8,}")


def run_import(data, connection, database_state):
    selected_matches = select_matches(data)
    selected_data = filter_dependent_data(
        data,
        selected_matches
    )

    print()
    print("=" * 80)
    print("IMPORT PREPARATION")
    print("=" * 80)
    print(f"\nSelected matches: {len(selected_matches):,}")
    print(f"Selected teams:   {len(selected_data['teams']):,}")
    print(f"Selected players: {len(selected_data['players']):,}")
    print(f"Selected venues:  {len({text(r['venue']) for r in selected_matches}):,}")
    print(f"Match-team rows:  {len(selected_data['match_team_stats']):,}")
    print(f"Player-match rows:{len(selected_data['player_match_performance']):,}")

    if IMPORT_LIMIT is None:
        print("Import mode: FULL DATASET")
    else:
        print(f"Import mode: PILOT ({IMPORT_LIMIT} matches)")

    # -------------------------------------------------------------------------
    # Teams
    # -------------------------------------------------------------------------
    team_mapping, _, _ = prepare_team_mapping(
        selected_data,
        database_state
    )

    # Competition can be created before seasons.
    competition = prepare_competition(database_state)
    competition = ensure_competition(
        connection,
        competition
    )

    team_created = insert_teams(
        connection,
        team_mapping
    )

    # -------------------------------------------------------------------------
    # Players
    # -------------------------------------------------------------------------
    player_mapping, _, _ = prepare_player_mapping(
        selected_data,
        database_state,
        team_mapping
    )

    # Team IDs now exist after insertion.
    for player in player_mapping.values():
        preferred_team = player.get("team_key")

        if preferred_team in team_mapping:
            player["team_id"] = team_mapping[preferred_team]["id"]

    player_created = insert_players(
        connection,
        player_mapping
    )

    # -------------------------------------------------------------------------
    # Venues
    # -------------------------------------------------------------------------
    venue_mapping = prepare_venue_mapping(
        selected_data,
        database_state
    )

    venue_created = insert_venues(
        connection,
        venue_mapping
    )

    # -------------------------------------------------------------------------
    # Seasons
    # -------------------------------------------------------------------------
    seasons, season_created = ensure_seasons(
        connection,
        competition,
        selected_data,
        database_state
    )

    # -------------------------------------------------------------------------
    # Matches
    # -------------------------------------------------------------------------
    (
        match_mapping,
        match_imported,
        match_reused,
    ) = insert_matches(
        connection,
        selected_data,
        team_mapping,
        venue_mapping,
        seasons,
        competition,
        database_state,
    )

    # -------------------------------------------------------------------------
    # Match team stats
    # -------------------------------------------------------------------------
    (
        match_team_inserted,
        match_team_skipped,
    ) = insert_match_team_stats(
        connection,
        selected_data,
        match_mapping,
        team_mapping,
    )

    # -------------------------------------------------------------------------
    # Player match performance
    # -------------------------------------------------------------------------
    (
        performance_inserted,
        performance_skipped,
    ) = insert_player_match_performance(
        connection,
        selected_data,
        match_mapping,
        player_mapping,
        team_mapping,
    )

    # -------------------------------------------------------------------------
    # Player season statistics
    # -------------------------------------------------------------------------
    if IMPORT_LIMIT is None:
        (
            statistics_inserted,
            statistics_skipped,
        ) = insert_player_statistics(
            connection,
            data,
            player_mapping,
            competition,
            seasons,
        )
    else:
        statistics_inserted = 0
        statistics_skipped = 0
        print()
        print("Player season statistics: SKIPPED during pilot import")

    print_import_summary(
        team_created,
        player_created,
        venue_created,
        season_created,
        match_imported,
        match_reused,
        match_team_inserted,
        match_team_skipped,
        performance_inserted,
        performance_skipped,
        statistics_inserted,
        statistics_skipped,
    )


# =============================================================================
# MAIN
# =============================================================================

def main():
    print()
    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL DATA -> MYSQL IMPORTER")
    print("=" * 80)

    print()
    print(f"DRY_RUN      = {DRY_RUN}")
    print(f"IMPORT_LIMIT = {IMPORT_LIMIT}")

    if not DRY_RUN:
        print()
        print("WARNING: DATABASE WRITE MODE IS ENABLED.")

    data = load_all_csvs()
    validate_csv_data(data)

    connection = connect_database()

    try:
        database_state = load_database_state(connection)

        if DRY_RUN:
            analyse(
                data,
                database_state
            )
        else:
            run_import(
                data,
                connection,
                database_state
            )

    except Exception as error:
        connection.rollback()
        print()
        print("=" * 80)
        print("IMPORT FAILED")
        print("=" * 80)
        print()
        print(f"{type(error).__name__}: {error}")
        raise

    finally:
        connection.close()

    print()
    print("=" * 80)
    print("DRY RUN COMPLETE" if DRY_RUN else "IPL IMPORT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

