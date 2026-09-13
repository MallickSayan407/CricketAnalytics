import csv
import getpass
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

import mysql.connector


# =============================================================================
# CRICKET ANALYTICS
# T20I CSV -> MYSQL IMPORTER
# =============================================================================
#
# SAFETY
# -------
# DRY_RUN = True
#     Analyse only. NO database writes.
#
# DRY_RUN = False
#     Perform database import.
#
# IMPORT_LIMIT = 10
#     Import first 10 T20I matches chronologically.
#
# IMPORT_LIMIT = None
#     Import complete T20I dataset.
#
# IMPORTANT
# ---------
# Competition:
#     International T20I
#
# Competition ID expected:
#     3
#
# Super Overs:
#     Already excluded from normal statistics by the processor.
#
# Gender:
#     Team identity is handled using (team_name, gender).
#
# Historical player teams:
#     Player.team represents a current/preferred team only.
#     Match-level historical team information is not stored in Player.
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
    "t20i"
)


DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "cricket_analytics",
    "user": "root",

    # You can replace this with os.getenv("CRICKET_DB_PASSWORD")
    # if you prefer not to keep the password in this file.
    "password": os.getenv("DB_PASSWORD"),
}


# =============================================================================
# SAFETY SWITCHES
# =============================================================================

# True  = no database writes
# False = actual import
DRY_RUN = False


# FIRST RUN:
# Keep this at 10.
#
# After successful pilot + audit:
# Change to:
#
# IMPORT_LIMIT = None
#
IMPORT_LIMIT = 10


# =============================================================================
# FILES
# =============================================================================

FILES = {
    "teams": os.path.join(
        PROCESSED_DIR,
        "teams.csv"
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
# CONSTANTS
# =============================================================================

EXPECTED_COMPETITION_NAME = "International T20I"
EXPECTED_COMPETITION_TYPE = "INTERNATIONAL"
EXPECTED_COMPETITION_FORMAT = "T20I"


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
        fail(
            f"Invalid integer value: {value}"
        )


def decimal(value, default=0.0):
    if value is None or str(value).strip() == "":
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        fail(
            f"Invalid decimal value: {value}"
        )


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

    return " ".join(
        value.lower().split()
    )


def team_key(name, gender):
    return (
        normalize_key(name),
        normalize_gender(gender)
    )


def parse_date(value):
    value = text(value)

    if not value:
        fail("Missing match date.")

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(
                value,
                fmt
            ).date()
        except ValueError:
            pass

    fail(
        f"Could not parse date: {value}"
    )


def unique_values(rows, column):
    return {
        text(row[column])
        for row in rows
        if text(row[column])
    }


def load_csv(path):
    if not os.path.exists(path):
        fail(
            f"CSV file not found:\n{path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


# =============================================================================
# CSV LOADING
# =============================================================================

def build_players_from_performance(data):
    """
    Build the player master dataset from player_match_performance.csv.

    The T20I processor intentionally does not create players.csv. The
    performance file already contains the stable Cricsheet player external ID,
    name, gender, and team association, so it is sufficient to construct the
    Player entities needed by this importer.

    Role is inferred from the career statistics file where possible:
      batting + bowling -> ALL_ROUNDER
      bowling only      -> BOWLER
      batting only      -> BATTER
      neither           -> OTHER
    """

    performance_rows = data["player_match_performance"]
    statistics_rows = data["player_statistics"]

    role_by_player = {}

    for row in statistics_rows:
        external_id = text(row.get("player_external_id"))

        if not external_id:
            continue

        batting_innings = integer(
            row.get("batting_innings"),
            0
        )
        bowling_innings = integer(
            row.get("bowling_innings"),
            0
        )

        if batting_innings > 0 and bowling_innings > 0:
            role = "ALL_ROUNDER"
        elif bowling_innings > 0:
            role = "BOWLER"
        elif batting_innings > 0:
            role = "BATTER"
        else:
            role = "OTHER"

        role_by_player[external_id] = role

    players = {}

    for row in performance_rows:
        external_id = text(row.get("player_external_id"))

        if not external_id:
            continue

        if external_id in players:
            continue

        players[external_id] = {
            "player_id": text(row.get("player_id")),
            "player_external_id": external_id,
            "player_name": (
                text(row.get("player_name"))
                or "Unknown Player"
            ),
            "gender": normalize_gender(
                row.get("gender")
            ),
            "team_name": text(row.get("team_name")),
            "role": role_by_player.get(
                external_id,
                "OTHER"
            ),
            "batting_style": None,
            "bowling_style": None,
        }

    return list(players.values())


def load_all_csv():
    print()
    print("=" * 80)
    print("LOADING PROCESSED T20I CSV FILES")
    print("=" * 80)

    data = {}

    for name, path in FILES.items():
        print(
            f"Loading {name:30s}: {path}"
        )

        data[name] = load_csv(path)

        print(
            f"  Rows: {len(data[name]):,}"
        )

    # The T20I processor does not generate players.csv. Build the player
    # master records from the processed player-match-performance dataset.
    data["players"] = build_players_from_performance(data)

    print(
        f"Building players from player_match_performance: "
        f"{len(data['players']):,} unique players"
    )

    return data


# =============================================================================
# CSV STRUCTURE VALIDATION
# =============================================================================

REQUIRED_COLUMNS = {
    "teams": {
        "team_id",
        "team_name",
        "gender",
    },

    "matches": {
        "match_id",
        "match_date",
        "gender",
        "match_type",
        "team1",
        "team2",
        "venue",
        "city",
        "country",
        "toss_winner",
        "toss_decision",
        "winner",
        "result_type",
        "result_description",
        "result_method",
        "eliminator",
        "overs",
    },

    "match_team_stats": {
        "match_id",
        "team_id",
        "team_name",
        "gender",
        "runs",
        "wickets",
        "total_balls",
        "allocated_balls",
        "fours",
        "sixes",
        "extras",
        "run_rate",
    },

    "player_match_performance": {
        "match_id",
        "player_id",
        "player_external_id",
        "player_name",
        "team_id",
        "team_name",
        "gender",
        "batting_runs",
        "balls_faced",
        "fours",
        "sixes",
        "batting_strike_rate",
        "not_out",
        "batted",
        "balls_bowled",
        "runs_conceded",
        "wickets",
        "bowling_economy",
        "maidens",
    },

    "player_statistics": {
        "player_id",
        "player_external_id",
        "player_name",
        "gender",
        "team_name",
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


def validate_columns(data, name, required):
    rows = data[name]

    if not rows:
        fail(
            f"{name}.csv contains no records."
        )

    actual = set(
        rows[0].keys()
    )

    missing = required - actual

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

    for name, required in REQUIRED_COLUMNS.items():
        validate_columns(
            data,
            name,
            required
        )

    # -------------------------------------------------------------------------
    # Match IDs
    # -------------------------------------------------------------------------

    match_ids = [
        text(row["match_id"])
        for row in data["matches"]
    ]

    if None in match_ids:
        fail(
            "matches.csv contains a row without match_id."
        )

    if len(match_ids) != len(set(match_ids)):
        fail(
            "matches.csv contains duplicate match_id values."
        )

    # -------------------------------------------------------------------------
    # Player external IDs
    # -------------------------------------------------------------------------

    player_external_ids = [
        text(row["player_external_id"])
        for row in data["players"]
    ]

    if None in player_external_ids:
        fail(
            "players.csv contains player without external ID."
        )

    if len(player_external_ids) != len(
        set(player_external_ids)
    ):
        fail(
            "players.csv contains duplicate player_external_id values."
        )

    # -------------------------------------------------------------------------
    # Match validation
    # -------------------------------------------------------------------------

    for row in data["matches"]:

        if text(row["match_type"]) != "T20":
            fail(
                "Non-T20 record found:\n"
                f"{row['match_id']} / "
                f"{row['match_type']}"
            )

        gender = normalize_gender(
            row["gender"]
        )

        if gender not in {
            "male",
            "female"
        }:
            fail(
                f"Unexpected gender in match "
                f"{row['match_id']}: {gender}"
            )

        parse_date(
            row["match_date"]
        )

    # -------------------------------------------------------------------------
    # Player performance validation
    # -------------------------------------------------------------------------

    for row in data["player_match_performance"]:

        wickets = integer(
            row["wickets"]
        )

        if wickets < 0 or wickets > 10:
            fail(
                "Invalid player wickets value:\n"
                f"{row['player_name']} / "
                f"{row['match_id']} / "
                f"{wickets}"
            )

    # -------------------------------------------------------------------------
    # Match-team validation
    # -------------------------------------------------------------------------

    for row in data["match_team_stats"]:

        runs = integer(
            row["runs"]
        )

        wickets = integer(
            row["wickets"]
        )

        total_balls = integer(
            row["total_balls"]
        )

        allocated_balls = integer(
            row["allocated_balls"]
        )

        if runs < 0:
            fail(
                f"Negative team runs: {row['match_id']}"
            )

        if wickets < 0 or wickets > 10:
            fail(
                f"Invalid team wickets: {row['match_id']}"
            )

        if total_balls < 0:
            fail(
                f"Negative total balls: {row['match_id']}"
            )

        if allocated_balls < 0:
            fail(
                f"Negative allocated balls: {row['match_id']}"
            )

    print()
    print("CSV structure and integrity: PASS")


# =============================================================================
# MYSQL CONNECTION
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
    print(
        f"Database: {DB_CONFIG['database']}"
    )

    return connection


# =============================================================================
# EXISTING DATABASE LOOKUPS
# =============================================================================

def get_existing_teams(cursor):

    cursor.execute(
        """
        SELECT
            id,
            name,
            short_name,
            country,
            gender
        FROM teams
        """
    )

    result = {}

    for row in cursor.fetchall():

        key = team_key(
            row[1],
            row[4]
        )

        result[key] = {
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
        SELECT
            id,
            external_id,
            name,
            role,
            team_id
        FROM players
        """
    )

    result = {}

    for row in cursor.fetchall():

        if row[1]:

            result[
                str(row[1])
            ] = {
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
        SELECT
            id,
            name,
            type,
            format
        FROM competitions
        """
    )

    result = {}

    for row in cursor.fetchall():

        result[
            normalize_key(row[1])
        ] = {
            "id": row[0],
            "name": row[1],
            "type": row[2],
            "format": row[3],
        }

    return result


def get_existing_seasons(cursor):

    cursor.execute(
        """
        SELECT
            id,
            name,
            start_year,
            end_year,
            competition_id
        FROM seasons
        """
    )

    result = {}

    for row in cursor.fetchall():

        result[
            (
                row[4],
                normalize_key(row[1])
            )
        ] = {
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
        SELECT
            id,
            name,
            city,
            country,
            capacity
        FROM venues
        """
    )

    result = {}

    for row in cursor.fetchall():

        result[
            normalize_key(row[1])
        ] = {
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
        SELECT
            id,
            external_id
        FROM matches
        WHERE external_id IS NOT NULL
        """
    )

    return {
        str(row[1]): row[0]
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

    print(
        f"\nExisting teams:             "
        f"{len(state['teams']):>8,}"
    )

    print(
        f"Existing players:           "
        f"{len(state['players']):>8,}"
    )

    print(
        f"Existing competitions:      "
        f"{len(state['competitions']):>8,}"
    )

    print(
        f"Existing seasons:           "
        f"{len(state['seasons']):>8,}"
    )

    print(
        f"Existing venues:            "
        f"{len(state['venues']):>8,}"
    )

    print(
        f"Existing imported matches:  "
        f"{len(state['matches']):>8,}"
    )

    return state


# =============================================================================
# MATCH SELECTION
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


def filter_dependent_data(
    data,
    selected_matches
):

    selected_ids = {
        str(row["match_id"])
        for row in selected_matches
    }

    filtered = dict(data)

    filtered["matches"] = selected_matches

    filtered["match_team_stats"] = [
        row
        for row in data["match_team_stats"]
        if str(row["match_id"])
        in selected_ids
    ]

    filtered["player_match_performance"] = [
        row
        for row in data["player_match_performance"]
        if str(row["match_id"])
        in selected_ids
    ]

    # Only players participating in selected matches.
    # The players list was derived from player_match_performance.csv.
    selected_player_ids = {
        text(row["player_external_id"])
        for row in filtered[
            "player_match_performance"
        ]
        if text(row["player_external_id"])
    }

    filtered["players"] = [
        row
        for row in data["players"]
        if text(row["player_external_id"])
        in selected_player_ids
    ]

    selected_team_keys = set()

    for row in selected_matches:

        gender = normalize_gender(
            row["gender"]
        )

        selected_team_keys.add(
            team_key(
                row["team1"],
                gender
            )
        )

        selected_team_keys.add(
            team_key(
                row["team2"],
                gender
            )
        )

    for row in filtered[
        "match_team_stats"
    ]:

        selected_team_keys.add(
            team_key(
                row["team_name"],
                row["gender"]
            )
        )

    for row in filtered[
        "player_match_performance"
    ]:

        selected_team_keys.add(
            team_key(
                row["team_name"],
                row["gender"]
            )
        )

    filtered["teams"] = [
        row
        for row in data["teams"]
        if team_key(
            row["team_name"],
            row["gender"]
        ) in selected_team_keys
    ]

    return filtered


# =============================================================================
# TEAM CODE GENERATION
# =============================================================================

KNOWN_CODES = {

    "Afghanistan": "AFG",
    "Australia": "AUS",
    "Bangladesh": "BAN",
    "Canada": "CAN",
    "England": "ENG",
    "India": "IND",
    "Ireland": "IRE",
    "Namibia": "NAM",
    "Nepal": "NEP",
    "Netherlands": "NED",
    "New Zealand": "NZL",
    "Pakistan": "PAK",
    "Scotland": "SCO",
    "South Africa": "RSA",
    "Sri Lanka": "SL",
    "United Arab Emirates": "UAE",
    "United States of America": "USA",
    "West Indies": "WI",
    "Zimbabwe": "ZIM",

    "Hong Kong": "HKG",
    "Hong Kong, China": "HKG",

    "Uganda": "UGA",
    "Tanzania": "TAN",
    "Kenya": "KEN",
    "Rwanda": "RWA",
    "Nigeria": "NGR",
    "Ghana": "GHA",
    "Botswana": "BOT",
    "Namibia": "NAM",
    "Malawi": "MWI",
    "Sierra Leone": "SLE",

    "Italy": "ITA",
    "Germany": "GER",
    "France": "FRA",
    "Spain": "ESP",
    "Portugal": "POR",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Denmark": "DEN",
    "Finland": "FIN",
    "Greece": "GRE",
    "Isle of Man": "IOM",
    "Jersey": "JER",
    "Guernsey": "GGY",

    "Bermuda": "BER",
    "Canada": "CAN",
    "Cayman Islands": "CAY",
    "Bahamas": "BAH",
    "Argentina": "ARG",
    "Brazil": "BRA",
    "Chile": "CHI",
    "Mexico": "MEX",
    "Panama": "PAN",
    "Costa Rica": "CRC",

    "Malaysia": "MAS",
    "Singapore": "SIN",
    "Thailand": "THA",
    "Indonesia": "INA",
    "Philippines": "PHI",
    "Japan": "JPN",
    "South Korea": "KOR",
    "South Korea": "KOR",

    "Nepal": "NEP",
    "Bhutan": "BHU",
    "Maldives": "MDV",

    "Oman": "OMA",
    "Qatar": "QAT",
    "Bahrain": "BHR",
    "Kuwait": "KUW",
    "Saudi Arabia": "KSA",

    "Papua New Guinea": "PNG",
    "Fiji": "FIJ",
    "Samoa": "SAM",
    "Vanuatu": "VAN",
    "Tonga": "TGA",
    "Cook Islands": "COK",
}


def generate_short_name(
    team_name,
    used_codes
):

    if team_name in KNOWN_CODES:

        original = KNOWN_CODES[
            team_name
        ][:3]

    else:

        letters = [
            ch.upper()
            for ch in team_name
            if ch.isalnum()
        ]

        original = "".join(
            letters[:3]
        )

        if len(original) < 3:

            original = (
                original + "XXX"
            )[:3]

    code = original
    counter = 1

    while code in used_codes:

        suffix = str(counter)

        prefix_length = (
            3 - len(suffix)
        )

        if prefix_length <= 0:

            fail(
                "Could not generate unique "
                f"3-character code for team: "
                f"{team_name}"
            )

        code = (
            original[:prefix_length]
            + suffix
        )

        counter += 1

    used_codes.add(code)

    return code


# =============================================================================
# TEAM MAPPING
# =============================================================================

def prepare_team_mapping(
    data,
    database_state
):

    existing = database_state[
        "teams"
    ]

    mapping = {}

    used_codes = {
        record["short_name"]
        for record in existing.values()
        if record.get("short_name")
    }

    code_owner = defaultdict(set)

    for record in existing.values():

        if record.get("short_name"):

            code_owner[
                normalize_key(
                    record["name"]
                )
            ].add(
                record["short_name"]
            )

    unique_teams = {}

    for row in data["teams"]:

        name = text(
            row["team_name"]
        )

        gender = normalize_gender(
            row["gender"]
        )

        if not name:
            continue

        key = team_key(
            name,
            gender
        )

        unique_teams[key] = {
            "name": name,
            "gender": gender,
        }

    existing_count = 0
    new_count = 0

    for key, info in sorted(
        unique_teams.items()
    ):

        name = info["name"]
        gender = info["gender"]

        if key in existing:

            record = dict(
                existing[key]
            )

            existing_count += 1

        else:

            name_key = normalize_key(
                name
            )

            if code_owner.get(
                name_key
            ):

                short_name = sorted(
                    code_owner[name_key]
                )[0]

            else:

                short_name = generate_short_name(
                    name,
                    used_codes
                )

                code_owner[
                    name_key
                ].add(
                    short_name
                )

            record = {
                "id": None,
                "name": name,
                "short_name": short_name,
                "country": name,
                "gender": gender,
            }

            new_count += 1

        mapping[key] = record

    return (
        mapping,
        existing_count,
        new_count
    )


def resolve_team(
    team_mapping,
    name,
    gender
):

    name = text(name)
    gender = normalize_gender(
        gender
    )

    key = team_key(
        name,
        gender
    )

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


# =============================================================================
# PLAYER MAPPING
# =============================================================================

def prepare_player_mapping(
    data,
    database_state,
    team_mapping
):

    existing = database_state[
        "players"
    ]

    mapping = {}

    # Determine preferred team from
    # most frequent match association.
    player_team_counts = defaultdict(
        Counter
    )

    for row in data[
        "player_match_performance"
    ]:

        external_id = text(
            row["player_external_id"]
        )

        team_name = text(
            row["team_name"]
        )

        gender = normalize_gender(
            row["gender"]
        )

        if external_id and team_name:

            player_team_counts[
                external_id
            ][
                team_key(
                    team_name,
                    gender
                )
            ] += 1

    existing_count = 0
    new_count = 0

    for row in data["players"]:

        external_id = text(
            row["player_external_id"]
        )

        if not external_id:

            fail(
                "Player has no external ID:\n"
                f"{row['player_name']}"
            )

        if external_id in mapping:
            continue

        # Existing global player.
        if external_id in existing:

            mapping[
                external_id
            ] = dict(
                existing[external_id]
            )

            existing_count += 1

            continue

        name = text(
            row["player_name"]
        )

        gender = normalize_gender(
            row["gender"]
        )

        preferred_team = None

        if external_id in player_team_counts:

            candidates = (
                player_team_counts[
                    external_id
                ]
            )

            if candidates:

                preferred_team = (
                    candidates
                    .most_common(1)[0][0]
                )

        if preferred_team is None:

            team_name = text(
                row["team_name"]
            )

            if team_name:

                preferred_team = team_key(
                    team_name,
                    gender
                )

        team_id = None

        if preferred_team in team_mapping:

            team_id = team_mapping[
                preferred_team
            ]["id"]

        mapping[
            external_id
        ] = {
            "id": None,
            "external_id": external_id,
            "name": name,
            "role": (
                text(row["role"])
                or "OTHER"
            ),
            "team_id": team_id,
            "team_key": preferred_team,
            "gender": gender,
            "batting_style": text(
                row["batting_style"]
            ),
            "bowling_style": text(
                row["bowling_style"]
            ),
        }

        new_count += 1

    return (
        mapping,
        existing_count,
        new_count
    )


# =============================================================================
# COMPETITION
# =============================================================================

def prepare_competition(
    database_state
):

    competition = database_state[
        "competitions"
    ].get(
        normalize_key(
            EXPECTED_COMPETITION_NAME
        )
    )

    if not competition:

        fail(
            "International T20I competition "
            "does not exist in the database."
        )

    if competition["id"] != 3:

        fail(
            "Unexpected International T20I "
            f"competition ID: "
            f"{competition['id']}. "
            "Expected ID 3."
        )

    if normalize_key(
        competition["type"]
    ) != normalize_key(
        EXPECTED_COMPETITION_TYPE
    ):

        fail(
            "International T20I competition "
            "type mismatch."
        )

    if normalize_key(
        competition["format"]
    ) != normalize_key(
        EXPECTED_COMPETITION_FORMAT
    ):

        fail(
            "International T20I competition "
            "format mismatch."
        )

    print()
    print(
        "Competition verified:"
    )
    print(
        f"  ID:     {competition['id']}"
    )
    print(
        f"  Name:   {competition['name']}"
    )
    print(
        f"  Type:   {competition['type']}"
    )
    print(
        f"  Format: {competition['format']}"
    )

    return competition


# =============================================================================
# VENUES
# =============================================================================

def prepare_venue_mapping(
    data,
    database_state
):

    existing = database_state[
        "venues"
    ]

    mapping = {}

    unique_venues = {}

    for row in data["matches"]:

        name = text(
            row["venue"]
        )

        if not name:
            continue

        key = normalize_key(
            name
        )

        if key not in unique_venues:

            unique_venues[key] = {
                "name": name,
                "city": text(
                    row["city"]
                ),
                "country": text(
                    row["country"]
                ),
            }

    for key, info in unique_venues.items():

        if key in existing:

            mapping[key] = dict(
                existing[key]
            )

        else:

            mapping[key] = {
                "id": None,
                "name": info["name"],
                "city": info["city"],
                "country": info["country"],
                "capacity": None,
            }

    return mapping


def insert_venues(
    connection,
    venue_mapping
):

    cursor = connection.cursor()

    created = 0

    try:

        for record in venue_mapping.values():

            if record["id"] is not None:
                continue

            cursor.execute(
                """
                INSERT INTO venues
                    (
                        name,
                        city,
                        country,
                        capacity
                    )
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    record["name"],
                    record["city"],
                    record["country"],
                    record["capacity"],
                )
            )

            record["id"] = (
                cursor.lastrowid
            )

            created += 1

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    return created


# =============================================================================
# INSERT TEAMS
# =============================================================================

def insert_teams(
    connection,
    team_mapping
):

    cursor = connection.cursor()

    created = 0

    try:

        for record in team_mapping.values():

            if record["id"] is not None:
                continue

            cursor.execute(
                """
                INSERT INTO teams
                    (
                        name,
                        short_name,
                        country,
                        gender
                    )
                VALUES
                    (%s, %s, %s, %s)
                """,
                (
                    record["name"],
                    record["short_name"],
                    record["country"],
                    record["gender"],
                )
            )

            record["id"] = (
                cursor.lastrowid
            )

            created += 1

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    return created


# =============================================================================
# INSERT PLAYERS
# =============================================================================

def insert_players(
    connection,
    player_mapping
):

    cursor = connection.cursor()

    created = 0

    try:

        for record in player_mapping.values():

            if record["id"] is not None:
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
                    record["name"],
                    record["external_id"],
                    record["role"],
                    record["batting_style"],
                    record["bowling_style"],
                    record["team_id"],
                )
            )

            record["id"] = (
                cursor.lastrowid
            )

            created += 1

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    return created


# =============================================================================
# SEASONS
# =============================================================================

def get_match_years(data):

    return sorted({
        parse_date(
            row["match_date"]
        ).year
        for row in data["matches"]
    })


def ensure_seasons(
    connection,
    competition,
    data,
    database_state
):

    seasons = dict(
        database_state["seasons"]
    )

    competition_id = (
        competition["id"]
    )

    years = get_match_years(
        data
    )

    print()
    print("=" * 80)
    print("SEASON SETUP")
    print("=" * 80)

    for year in years:

        key = (
            competition_id,
            str(year).lower()
        )

        if key in seasons:
            continue

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
                    str(year),
                    year,
                    year,
                    competition_id,
                )
            )

            season_id = (
                cursor.lastrowid
            )

            seasons[key] = {
                "id": season_id,
                "name": str(year),
                "start_year": year,
                "end_year": year,
                "competition_id":
                    competition_id,
            }

            connection.commit()

            print(
                f"  Created T20I season: "
                f"{year}"
            )

        except Exception:

            connection.rollback()
            raise

        finally:

            cursor.close()

    # -------------------------------------------------------------------------
    # CAREER season
    # -------------------------------------------------------------------------

    career_key = (
        competition_id,
        "career"
    )

    min_year = (
        min(years)
        if years
        else None
    )

    max_year = (
        max(years)
        if years
        else None
    )

    if career_key not in seasons:

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
                    "CAREER",
                    min_year,
                    max_year,
                    competition_id,
                )
            )

            season_id = (
                cursor.lastrowid
            )

            seasons[
                career_key
            ] = {
                "id": season_id,
                "name": "CAREER",
                "start_year": min_year,
                "end_year": max_year,
                "competition_id":
                    competition_id,
            }

            connection.commit()

            print(
                "  Created T20I CAREER season"
            )

        except Exception:

            connection.rollback()
            raise

        finally:

            cursor.close()

    else:

        career = seasons[
            career_key
        ]

        if (
            career["start_year"]
            != min_year
            or
            career["end_year"]
            != max_year
        ):

            cursor = connection.cursor()

            try:

                cursor.execute(
                    """
                    UPDATE seasons
                    SET
                        start_year = %s,
                        end_year = %s
                    WHERE id = %s
                    """,
                    (
                        min_year,
                        max_year,
                        career["id"],
                    )
                )

                connection.commit()

                career[
                    "start_year"
                ] = min_year

                career[
                    "end_year"
                ] = max_year

                print(
                    "  Updated T20I CAREER "
                    f"range: {min_year}-"
                    f"{max_year}"
                )

            except Exception:

                connection.rollback()
                raise

            finally:

                cursor.close()

    return seasons


# =============================================================================
# MATCH STATUS
# =============================================================================

def normalize_match_status(
    result_type,
    winner
):

    result_type = normalize_key(
        result_type
    )

    if result_type == "no_result":
        return "NO_RESULT"

    if result_type == "tied":
        return "COMPLETED"

    if winner:
        return "COMPLETED"

    return "COMPLETED"


# =============================================================================
# INSERT MATCHES
# =============================================================================

def insert_matches(
    connection,
    data,
    team_mapping,
    venue_mapping,
    seasons,
    competition,
    existing_matches
):

    cursor = connection.cursor()

    match_mapping = {}

    imported = 0
    reused = 0

    try:

        for row in data["matches"]:

            external_id = text(
                row["match_id"]
            )

            if not external_id:

                fail(
                    "Match has no match_id."
                )

            # Existing match.
            if external_id in existing_matches:

                match_mapping[
                    external_id
                ] = existing_matches[
                    external_id
                ]

                reused += 1

                continue

            gender = normalize_gender(
                row["gender"]
            )

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

            venue_name = text(
                row["venue"]
            )

            venue = venue_mapping.get(
                normalize_key(
                    venue_name
                )
            )

            if not venue or venue["id"] is None:

                fail(
                    "Could not resolve venue:\n"
                    f"{venue_name}"
                )

            match_date = parse_date(
                row["match_date"]
            )

            year = match_date.year

            season_key = (
                competition["id"],
                str(year).lower()
            )

            if season_key not in seasons:

                fail(
                    f"No T20I season found "
                    f"for year {year}"
                )

            season = seasons[
                season_key
            ]

            # -----------------------------------------------------------------
            # Toss winner
            # -----------------------------------------------------------------

            toss_winner = None

            toss_winner_name = text(
                row["toss_winner"]
            )

            if toss_winner_name:

                toss_key = team_key(
                    toss_winner_name,
                    gender
                )

                if toss_key in team_mapping:

                    toss_winner = (
                        team_mapping[
                            toss_key
                        ]
                    )

            # -----------------------------------------------------------------
            # Match winner
            # -----------------------------------------------------------------

            winner = None

            winner_name = text(
                row["winner"]
            )

            if winner_name:

                winner_key = team_key(
                    winner_name,
                    gender
                )

                if winner_key in team_mapping:

                    winner = (
                        team_mapping[
                            winner_key
                        ]
                    )

                else:

                    print(
                        "  Warning: unresolved "
                        "winner "
                        f"'{winner_name}' "
                        f"for match "
                        f"{external_id}; "
                        "storing NULL."
                    )

            match_status = (
                normalize_match_status(
                    row["result_type"],
                    winner_name
                )
            )

            result_description = text(
                row["result_description"]
            )

            # Stage is not supplied by the CSV.
            # International T20I is treated as League
            # unless later tournament metadata is added.
            stage = "League"

            cursor.execute(
                """
                INSERT INTO matches
                    (
                        external_id,
                        match_date,
                        match_status,
                        stage,
                        counted_in_standings,
                        toss_decision,
                        result_description,
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
                        %s, %s, %s, %s
                    )
                """,
                (
                    external_id,
                    match_date,
                    match_status,
                    stage,
                    True,
                    text(
                        row["toss_decision"]
                    ),
                    result_description,
                    competition["id"],
                    season["id"],
                    venue["id"],
                    team1["id"],
                    team2["id"],
                    (
                        toss_winner["id"]
                        if toss_winner
                        else None
                    ),
                    (
                        winner["id"]
                        if winner
                        else None
                    ),
                )
            )

            db_match_id = (
                cursor.lastrowid
            )

            match_mapping[
                external_id
            ] = db_match_id

            imported += 1

            if imported % 100 == 0:

                print(
                    f"  Matches imported: "
                    f"{imported:,}"
                )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    return (
        match_mapping,
        imported,
        reused
    )


# =============================================================================
# EXISTING CHILD RECORDS
# =============================================================================

def get_existing_match_team_stats(
    cursor
):

    cursor.execute(
        """
        SELECT
            match_id,
            team_id
        FROM match_team_stats
        """
    )

    return {
        (
            row[0],
            row[1]
        )
        for row in cursor.fetchall()
    }


def get_existing_player_match_performance(
    cursor
):

    cursor.execute(
        """
        SELECT
            match_id,
            player_id
        FROM player_match_performance
        """
    )

    return {
        (
            row[0],
            row[1]
        )
        for row in cursor.fetchall()
    }


# =============================================================================
# MATCH TEAM STATS
# =============================================================================

def insert_match_team_stats(
    connection,
    data,
    match_mapping,
    team_mapping
):

    cursor = connection.cursor()

    existing = (
        get_existing_match_team_stats(
            cursor
        )
    )

    inserted = 0
    skipped = 0

    try:

        for row in data[
            "match_team_stats"
        ]:

            external_match_id = text(
                row["match_id"]
            )

            if (
                external_match_id
                not in match_mapping
            ):
                continue

            db_match_id = (
                match_mapping[
                    external_match_id
                ]
            )

            gender = normalize_gender(
                row["gender"]
            )

            team = resolve_team(
                team_mapping,
                row["team_name"],
                gender
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
                        allocated_balls,
                        fours,
                        sixes,
                        extras,
                        run_rate
                    )
                VALUES
                    (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s
                    )
                """,
                (
                    db_match_id,
                    team["id"],
                    integer(row["runs"]),
                    integer(row["wickets"]),
                    integer(
                        row["total_balls"]
                    ),
                    integer(
                        row["allocated_balls"]
                    ),
                    integer(row["fours"]),
                    integer(row["sixes"]),
                    integer(row["extras"]),
                    decimal(row["run_rate"]),
                )
            )

            existing.add(
                unique_key
            )

            inserted += 1

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    connection.commit()

    return (
        inserted,
        skipped
    )


# =============================================================================
# PLAYER MATCH PERFORMANCE
# =============================================================================

def insert_player_match_performance(
    connection,
    data,
    match_mapping,
    player_mapping
):

    cursor = connection.cursor()

    existing = (
        get_existing_player_match_performance(
            cursor
        )
    )

    inserted = 0
    skipped = 0

    try:

        for row in data[
            "player_match_performance"
        ]:

            external_match_id = text(
                row["match_id"]
            )

            if (
                external_match_id
                not in match_mapping
            ):
                continue

            external_player_id = text(
                row["player_external_id"]
            )

            if (
                external_player_id
                not in player_mapping
            ):

                fail(
                    "Player performance "
                    "references unknown player:\n"
                    f"{external_player_id}"
                )

            db_match_id = (
                match_mapping[
                    external_match_id
                ]
            )

            player = player_mapping[
                external_player_id
            ]

            if player["id"] is None:

                fail(
                    "Player has no database ID:\n"
                    f"{external_player_id}"
                )

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
                        %s, %s, %s
                    )
                """,
                (
                    db_match_id,
                    player["id"],
                    integer(
                        row["batting_runs"]
                    ),
                    integer(
                        row["balls_faced"]
                    ),
                    integer(
                        row["fours"]
                    ),
                    integer(
                        row["sixes"]
                    ),
                    decimal(
                        row[
                            "batting_strike_rate"
                        ]
                    ),
                    boolean(
                        row["not_out"]
                    ),
                    integer(
                        row["balls_bowled"]
                    ),
                    integer(
                        row["runs_conceded"]
                    ),
                    integer(
                        row["wickets"]
                    ),
                    decimal(
                        row[
                            "bowling_economy"
                        ]
                    ),
                    integer(
                        row["maidens"]
                    ),
                )
            )

            existing.add(
                unique_key
            )

            inserted += 1

            if inserted % 1000 == 0:

                print(
                    f"  Player performances: "
                    f"{inserted:,}"
                )

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    return (
        inserted,
        skipped
    )


# =============================================================================
# PLAYER CAREER STATISTICS
# =============================================================================

def get_existing_player_statistics(
    cursor,
    competition_id,
    career_season_id
):

    cursor.execute(
        """
        SELECT
            player_id,
            competition_id,
            season_id,
            scope
        FROM player_statistics
        WHERE competition_id = %s
          AND season_id = %s
          AND scope = 'CAREER'
        """,
        (
            competition_id,
            career_season_id,
        )
    )

    return {
        (
            row[0],
            row[1],
            row[2],
            row[3]
        )
        for row in cursor.fetchall()
    }


def insert_player_statistics(
    connection,
    data,
    player_mapping,
    competition,
    seasons
):

    career_season = seasons[
        (
            competition["id"],
            "career"
        )
    ]

    cursor = connection.cursor()

    existing = (
        get_existing_player_statistics(
            cursor,
            competition["id"],
            career_season["id"]
        )
    )

    inserted = 0
    skipped = 0

    try:

        for row in data[
            "player_statistics"
        ]:

            external_id = text(
                row["player_external_id"]
            )

            if external_id not in player_mapping:
                continue

            player = player_mapping[
                external_id
            ]

            if player["id"] is None:

                fail(
                    "Player statistics references "
                    "player without database ID:\n"
                    f"{external_id}"
                )

            unique_key = (
                player["id"],
                competition["id"],
                career_season["id"],
                "CAREER"
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
                    career_season["id"],
                    "CAREER",
                    integer(
                        row["matches"]
                    ),
                    integer(
                        row["batting_innings"]
                    ),
                    integer(
                        row["runs"]
                    ),
                    integer(
                        row["balls_faced"]
                    ),
                    integer(
                        row["highest_score"]
                    ),
                    integer(
                        row["not_outs"]
                    ),
                    integer(
                        row["fours"]
                    ),
                    integer(
                        row["sixes"]
                    ),
                    integer(
                        row["fifties"]
                    ),
                    integer(
                        row["centuries"]
                    ),
                    decimal(
                        row["batting_average"]
                    ),
                    decimal(
                        row["strike_rate"]
                    ),
                    integer(
                        row["bowling_innings"]
                    ),
                    integer(
                        row["balls_bowled"]
                    ),
                    integer(
                        row["wickets"]
                    ),
                    integer(
                        row["runs_conceded"]
                    ),
                    decimal(
                        row["economy"]
                    ),
                    decimal(
                        row["bowling_average"]
                    ),
                    integer(
                        row[
                            "best_bowling_wickets"
                        ]
                    ),
                    integer(
                        row["five_wicket_hauls"]
                    ),
                )
            )

            existing.add(
                unique_key
            )

            inserted += 1

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        cursor.close()

    return (
        inserted,
        skipped
    )


# =============================================================================
# IMPORT SUMMARY
# =============================================================================

def print_import_summary(
    team_created,
    player_created,
    venue_created,
    match_imported,
    match_reused,
    match_team_inserted,
    match_team_skipped,
    performance_inserted,
    performance_skipped,
    statistics_inserted,
    statistics_skipped
):

    print()
    print("=" * 80)
    print("IMPORT RESULT")
    print("=" * 80)

    print()
    print("BASE ENTITIES")

    print(
        f"  Teams created:             "
        f"{team_created:>8,}"
    )

    print(
        f"  Players created:           "
        f"{player_created:>8,}"
    )

    print(
        f"  Venues created:            "
        f"{venue_created:>8,}"
    )

    print()
    print("MATCHES")

    print(
        f"  Matches imported:          "
        f"{match_imported:>8,}"
    )

    print(
        f"  Existing matches reused:   "
        f"{match_reused:>8,}"
    )

    print()
    print("MATCH TEAM STATS")

    print(
        f"  Inserted:                  "
        f"{match_team_inserted:>8,}"
    )

    print(
        f"  Already existed:           "
        f"{match_team_skipped:>8,}"
    )

    print()
    print("PLAYER MATCH PERFORMANCE")

    print(
        f"  Inserted:                  "
        f"{performance_inserted:>8,}"
    )

    print(
        f"  Already existed:           "
        f"{performance_skipped:>8,}"
    )

    print()
    print("PLAYER CAREER STATISTICS")

    print(
        f"  Inserted:                  "
        f"{statistics_inserted:>8,}"
    )

    print(
        f"  Already existed:           "
        f"{statistics_skipped:>8,}"
    )


# =============================================================================
# IMPORT PIPELINE
# =============================================================================

def run_import(
    data,
    connection,
    database_state
):

    print()
    print("=" * 80)
    print("IMPORT PREPARATION")
    print("=" * 80)

    selected_matches = select_matches(
        data
    )

    selected_data = (
        filter_dependent_data(
            data,
            selected_matches
        )
    )

    print()
    print(
        f"Selected matches: "
        f"{len(selected_matches):,}"
    )

    print(
        f"Selected teams:   "
        f"{len(selected_data['teams']):,}"
    )

    print(
        f"Selected players: "
        f"{len(selected_data['players']):,}"
    )

    print(
        f"Selected venues:  "
        f"{len(unique_values(selected_data['matches'], 'venue')):,}"
    )

    print(
        f"Match-team rows:  "
        f"{len(selected_data['match_team_stats']):,}"
    )

    print(
        f"Player-match rows:"
        f"{len(selected_data['player_match_performance']):,}"
    )

    if IMPORT_LIMIT is None:

        print(
            "Import mode: FULL DATASET"
        )

    else:

        print(
            f"Import mode: PILOT "
            f"({IMPORT_LIMIT} matches)"
        )

    # -------------------------------------------------------------------------
    # TEAM MAPPING
    # -------------------------------------------------------------------------

    (
        team_mapping,
        existing_teams,
        new_teams
    ) = prepare_team_mapping(
        selected_data,
        database_state
    )

    print()
    print(
        f"Team identities: "
        f"{len(team_mapping):,} "
        f"({existing_teams:,} existing, "
        f"{new_teams:,} new)"
    )

    # -------------------------------------------------------------------------
    # COMPETITION
    # -------------------------------------------------------------------------

    competition = (
        prepare_competition(
            database_state
        )
    )

    # -------------------------------------------------------------------------
    # TEAMS
    # -------------------------------------------------------------------------

    team_created = insert_teams(
        connection,
        team_mapping
    )

    # -------------------------------------------------------------------------
    # PLAYERS
    # -------------------------------------------------------------------------

    (
        player_mapping,
        existing_players,
        new_players
    ) = prepare_player_mapping(
        selected_data,
        database_state,
        team_mapping
    )

    print(
        f"Players selected: "
        f"{len(player_mapping):,} "
        f"({existing_players:,} existing, "
        f"{new_players:,} new)"
    )

    # Update team IDs after team insertion.
    for player in player_mapping.values():

        team_key_value = (
            player.get("team_key")
        )

        if (
            team_key_value
            in team_mapping
        ):

            player["team_id"] = (
                team_mapping[
                    team_key_value
                ]["id"]
            )

    player_created = insert_players(
        connection,
        player_mapping
    )

    # -------------------------------------------------------------------------
    # VENUES
    # -------------------------------------------------------------------------

    venue_mapping = (
        prepare_venue_mapping(
            selected_data,
            database_state
        )
    )

    venue_created = insert_venues(
        connection,
        venue_mapping
    )

    # -------------------------------------------------------------------------
    # SEASONS
    # -------------------------------------------------------------------------

    seasons = ensure_seasons(
        connection,
        competition,
        selected_data,
        database_state
    )

    # -------------------------------------------------------------------------
    # MATCHES
    # -------------------------------------------------------------------------

    (
        match_mapping,
        match_imported,
        match_reused
    ) = insert_matches(
        connection,
        selected_data,
        team_mapping,
        venue_mapping,
        seasons,
        competition,
        database_state["matches"]
    )

    # -------------------------------------------------------------------------
    # MATCH TEAM STATS
    # -------------------------------------------------------------------------

    (
        match_team_inserted,
        match_team_skipped
    ) = insert_match_team_stats(
        connection,
        selected_data,
        match_mapping,
        team_mapping
    )

    # -------------------------------------------------------------------------
    # PLAYER MATCH PERFORMANCE
    # -------------------------------------------------------------------------

    (
        performance_inserted,
        performance_skipped
    ) = insert_player_match_performance(
        connection,
        selected_data,
        match_mapping,
        player_mapping
    )

    # -------------------------------------------------------------------------
    # PLAYER CAREER STATISTICS
    # -------------------------------------------------------------------------

    (
        statistics_inserted,
        statistics_skipped
    ) = insert_player_statistics(
        connection,
        selected_data,
        player_mapping,
        competition,
        seasons
    )

    print_import_summary(
        team_created,
        player_created,
        venue_created,
        match_imported,
        match_reused,
        match_team_inserted,
        match_team_skipped,
        performance_inserted,
        performance_skipped,
        statistics_inserted,
        statistics_skipped
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print()
    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("T20I CSV -> MYSQL IMPORTER")
    print("=" * 80)

    print()
    print(
        f"Processed directory:\n"
        f"{PROCESSED_DIR}"
    )

    print()
    print(
        f"DRY_RUN = {DRY_RUN}"
    )

    print(
        f"IMPORT_LIMIT = {IMPORT_LIMIT}"
    )

    # -------------------------------------------------------------------------
    # Load CSV
    # -------------------------------------------------------------------------

    data = load_all_csv()

    # -------------------------------------------------------------------------
    # Validate CSV
    # -------------------------------------------------------------------------

    validate_csv_data(
        data
    )

    # -------------------------------------------------------------------------
    # DRY RUN
    # -------------------------------------------------------------------------

    if DRY_RUN:

        print()
        print("=" * 80)
        print("DRY RUN COMPLETE")
        print("=" * 80)
        print(
            "No database writes were performed."
        )
        return

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------

    connection = connect_database()

    try:

        database_state = (
            load_database_state(
                connection
            )
        )

        run_import(
            data,
            connection,
            database_state
        )

        print()
        print("=" * 80)
        print("T20I IMPORT COMPLETE")
        print("=" * 80)

    except Exception as error:

        print()
        print("=" * 80)
        print("T20I IMPORT FAILED")
        print("=" * 80)

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        connection.rollback()

        raise

    finally:

        connection.close()

        print()
        print(
            "MySQL connection closed."
        )


if __name__ == "__main__":
    main()
