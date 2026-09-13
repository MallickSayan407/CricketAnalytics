import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

import mysql.connector


# =============================================================================
# CRICKET ANALYTICS
# TEST CSV -> MYSQL IMPORTER (V7) (V6) (V5) (V4)
# =============================================================================
#
# IMPORTANT:
# The Test processor intentionally creates ONLY these five CSVs:
#
#   teams.csv
#   matches.csv
#   match_team_stats.csv
#   player_match_performance.csv
#   player_statistics.csv
#
# There is NO players.csv or venues.csv. Players and venues are therefore
# derived from the other CSVs, exactly like the T20I/ODI importer architecture.
#
# SAFETY:
#   DRY_RUN = True  -> no database writes
#   DRY_RUN = False -> database import
#
# PILOT:
#   IMPORT_LIMIT = 10
#   After pilot verification, change to None for all 918 Tests.
# =============================================================================


# =============================================================================
# CONFIGURATION
# =============================================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = os.path.join(
    BASE_DIR,
    "processed",
    "test"
)

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "cricket_analytics",
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
}

DRY_RUN = False

# FIRST RUN = 10-match pilot.
# Change to None only after the pilot is verified.
IMPORT_LIMIT = 10

EXPECTED_COMPETITION_NAME = "International Test"
EXPECTED_COMPETITION_TYPE = "INTERNATIONAL"
EXPECTED_COMPETITION_FORMAT = "TEST"


FILES = {
    "teams": os.path.join(PROCESSED_DIR, "teams.csv"),
    "matches": os.path.join(PROCESSED_DIR, "matches.csv"),
    "match_team_stats": os.path.join(PROCESSED_DIR, "match_team_stats.csv"),
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


def parse_date(value):
    value = text(value)

    if not value:
        fail("Missing match date.")

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    fail(f"Could not parse date: {value}")


def load_csv(path):
    if not os.path.exists(path):
        fail(f"CSV file not found:\n{path}")

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    if not rows:
        fail(f"CSV is empty:\n{path}")

    return rows


def require_columns(rows, name, columns):
    actual = set(rows[0].keys())

    missing = [
        column
        for column in columns
        if column not in actual
    ]

    if missing:
        fail(
            f"{name}.csv is missing columns:\n"
            + "\n".join(f"  - {x}" for x in missing)
        )


def team_key(name, gender):
    return (
        normalize_key(name),
        normalize_gender(gender)
    )


def unique_short_name(name, used):
    # Prefer a few meaningful abbreviations for international teams.
    preferred = {
        "Australia": "AUS",
        "Bangladesh": "BAN",
        "England": "ENG",
        "India": "IND",
        "Ireland": "IRE",
        "New Zealand": "NZ",
        "Pakistan": "PAK",
        "South Africa": "SA",
        "Sri Lanka": "SL",
        "West Indies": "WI",
        "Zimbabwe": "ZIM",
    }

    base = preferred.get(name)

    if not base:
        letters = [
            c.upper()
            for c in name
            if c.isalnum()
        ]
        base = "".join(letters[:3]) or "TEAM"

    base = base[:10]

    candidate = base
    counter = 1

    while candidate in used:
        suffix = str(counter)
        candidate = base[:10 - len(suffix)] + suffix
        counter += 1

    used.add(candidate)
    return candidate


# =============================================================================
# LOAD
# =============================================================================

print("=" * 80)
print("CRICKET ANALYTICS")
print("TEST CSV -> MYSQL IMPORTER")
print("=" * 80)

print()
print("Processed directory:")
print(PROCESSED_DIR)

print()
print(f"DRY_RUN = {DRY_RUN}")
print(f"IMPORT_LIMIT = {IMPORT_LIMIT}")

print()
print("=" * 80)
print("LOADING PROCESSED TEST CSV FILES")
print("=" * 80)

data = {}

for name, path in FILES.items():
    print(f"Loading {name:<32}: {path}")
    rows = load_csv(path)
    data[name] = rows
    print(f"  Rows: {len(rows):,}")

teams = data["teams"]
matches_all = data["matches"]
match_team_all = data["match_team_stats"]
player_match_all = data["player_match_performance"]
career_stats = data["player_statistics"]

require_columns(
    teams,
    "teams",
    ["team_name", "gender"]
)

require_columns(
    matches_all,
    "matches",
    [
        "match_id",
        "match_date",
        "gender",
        "team1",
        "team2",
        "winner",
        "result_type",
        "result_description",
    ]
)

require_columns(
    match_team_all,
    "match_team_stats",
    [
        "match_id",
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
    ]
)

require_columns(
    player_match_all,
    "player_match_performance",
    [
        "match_id",
        "player_external_id",
        "player_name",
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
    ]
)

require_columns(
    career_stats,
    "player_statistics",
    [
        "player_external_id",
        "player_name",
        "gender",
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
    ]
)


# =============================================================================
# PILOT SELECTION
# =============================================================================

matches = list(matches_all)

if IMPORT_LIMIT is not None:
    matches = matches[:IMPORT_LIMIT]

selected_ids = {
    text(row["match_id"])
    for row in matches
}

match_team = [
    row
    for row in match_team_all
    if text(row["match_id"]) in selected_ids
]

player_match = [
    row
    for row in player_match_all
    if text(row["match_id"]) in selected_ids
]

selected_team_names = {
    (
        text(row["team_name"]),
        normalize_gender(row.get("gender"))
    )
    for row in match_team
}

selected_player_ids = {
    text(row["player_external_id"])
    for row in player_match
    if text(row["player_external_id"])
}

# Career statistics are global Test career rows. We only need players that
# appear in the selected pilot matches.
career_selected = [
    row
    for row in career_stats
    if text(row["player_external_id"]) in selected_player_ids
]

selected_venue_names = {
    text(row.get("venue"))
    for row in matches
    if text(row.get("venue"))
}

print()
print("=" * 80)
print("IMPORT PREPARATION")
print("=" * 80)
print(f"Selected matches:       {len(matches):,}")
print(f"Selected teams:         {len(selected_team_names):,}")
print(f"Selected players:       {len(selected_player_ids):,}")
print(f"Selected venues:        {len(selected_venue_names):,}")
print(f"Match-team rows:        {len(match_team):,}")
print(f"Player-match rows:      {len(player_match):,}")
print(f"Career-stat rows:       {len(career_selected):,}")

if IMPORT_LIMIT is None:
    print("Import mode: FULL (918 Test matches)")
else:
    print(f"Import mode: PILOT ({IMPORT_LIMIT} matches)")


# =============================================================================
# DATABASE
# =============================================================================

if DRY_RUN:
    print()
    print("=" * 80)
    print("DRY RUN")
    print("=" * 80)
    print("CSV structure validation passed.")
    print("No database connection or writes performed.")
    sys.exit(0)


try:
    connection = mysql.connector.connect(**DB_CONFIG)
except Exception as error:
    fail(
        "Could not connect to MySQL:\n"
        f"{type(error).__name__}: {error}"
    )

connection.autocommit = False
cursor = connection.cursor(dictionary=True)

print()
print("=" * 80)
print("MYSQL CONNECTION")
print("=" * 80)
print("MySQL connection: PASS")
print("Database:", DB_CONFIG["database"])


def query_one(sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchone()


def query_all(sql, params=()):
    cursor.execute(sql, params)
    return cursor.fetchall()


def get_competition():
    row = query_one(
        """
        SELECT id, name, type, format
        FROM competitions
        WHERE name = %s
        LIMIT 1
        """,
        (EXPECTED_COMPETITION_NAME,)
    )

    if not row:
        fail(
            f"Competition '{EXPECTED_COMPETITION_NAME}' "
            "was not found in MySQL."
        )

    return row


competition = get_competition()

if str(competition["type"]).upper() != EXPECTED_COMPETITION_TYPE:
    fail(
        "Competition type mismatch:\n"
        f"Expected: {EXPECTED_COMPETITION_TYPE}\n"
        f"Actual:   {competition['type']}"
    )

if str(competition["format"]).upper() not in {
    EXPECTED_COMPETITION_FORMAT,
    "TEST",
}:
    fail(
        "Competition format mismatch:\n"
        f"Expected: TEST\n"
        f"Actual:   {competition['format']}"
    )

competition_id = competition["id"]

print()
print("Competition verified:")
print("  ID:    ", competition_id)
print("  Name:  ", competition["name"])
print("  Type:  ", competition["type"])
print("  Format:", competition["format"])


# =============================================================================
# EXISTING DATABASE COUNTS
# =============================================================================

print()
print("=" * 80)
print("EXISTING DATABASE STATE")
print("=" * 80)

for table in [
    "teams",
    "players",
    "competitions",
    "seasons",
    "venues",
    "matches",
]:
    try:
        value = query_one(f"SELECT COUNT(*) AS c FROM {table}")["c"]
        print(f"{table:<25}: {value:,}")
    except Exception as error:
        fail(
            f"Could not inspect table '{table}': "
            f"{type(error).__name__}: {error}"
        )


# =============================================================================
# TEAM MAPPING
# =============================================================================

print()
print("=" * 80)
print("TEAM MAPPING")
print("=" * 80)

team_mapping = {}

existing_short_rows = query_all(
    "SELECT short_name FROM teams WHERE short_name IS NOT NULL"
)

used_short_names = {
    text(row["short_name"])
    for row in existing_short_rows
    if text(row["short_name"])
}

teams_created = 0
teams_reused = 0

for name, gender in sorted(selected_team_names):
    row = query_one(
        """
        SELECT id, name, short_name, gender
        FROM teams
        WHERE name = %s
          AND gender = %s
        ORDER BY id
        LIMIT 1
        """,
        (name, gender)
    )

    if row:
        team_mapping[(name, gender)] = row["id"]
        teams_reused += 1
        continue

    short_name = unique_short_name(name, used_short_names)

    cursor.execute(
        """
        INSERT INTO teams
        (name, short_name, gender)
        VALUES (%s, %s, %s)
        """,
        (name, short_name, gender)
    )

    team_mapping[(name, gender)] = cursor.lastrowid
    teams_created += 1

print("Teams reused:", teams_reused)
print("Teams created:", teams_created)


# =============================================================================
# PLAYER MAPPING
# =============================================================================

print()
print("=" * 80)
print("PLAYER MAPPING")
print("=" * 80)

# Best metadata source = player-match rows.
player_meta = {}

for row in player_match_all:
    external_id = text(row["player_external_id"])

    if external_id and external_id not in player_meta:
        player_meta[external_id] = row

player_mapping = {}

players_created = 0
players_reused = 0

for external_id in sorted(selected_player_ids):
    existing = query_one(
        """
        SELECT id, external_id, name, role, batting_style,
               bowling_style, team_id
        FROM players
        WHERE external_id = %s
        LIMIT 1
        """,
        (external_id,)
    )

    if existing:
        player_mapping[external_id] = existing["id"]
        players_reused += 1
        continue

    meta = player_meta.get(external_id)

    if not meta:
        fail(
            f"No player metadata for external ID: {external_id}"
        )

    name = text(meta["player_name"]) or "Unknown Player"
    gender = normalize_gender(meta.get("gender"))

    # MySQL requires players.role to be NOT NULL. Some Test records do not
    # provide a role, so use a neutral fallback instead of inventing a role.
    role = text(meta.get("role")) or "Cricketer"
    batting_style = text(meta.get("batting_style"))
    bowling_style = text(meta.get("bowling_style"))

    team_name = text(meta.get("team_name"))
    team_id = None

    if team_name:
        team_id = team_mapping.get(
            (team_name, gender)
        )

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
        (%s,%s,%s,%s,%s,%s)
        """,
        (
            name,
            external_id,
            role,
            batting_style,
            bowling_style,
            team_id,
        )
    )

    player_mapping[external_id] = cursor.lastrowid
    players_created += 1

print("Players reused:", players_reused)
print("Players created:", players_created)


# =============================================================================
# VENUE MAPPING
# =============================================================================

print()
print("=" * 80)
print("VENUE MAPPING")
print("=" * 80)

venue_mapping = {}

venues_created = 0
venues_reused = 0

for venue_name in sorted(selected_venue_names):
    existing = query_one(
        """
        SELECT id, name
        FROM venues
        WHERE name = %s
        ORDER BY id
        LIMIT 1
        """,
        (venue_name,)
    )

    if existing:
        venue_mapping[venue_name] = existing["id"]
        venues_reused += 1
        continue

    # City/country are available in matches.csv.
    city = None
    country = None

    for match_row in matches_all:
        if text(match_row.get("venue")) == venue_name:
            city = text(match_row.get("city"))
            country = text(match_row.get("country"))
            break

    # The current project Venue entity uses name/city/country.
    cursor.execute(
        """
        INSERT INTO venues
        (name, city, country)
        VALUES (%s,%s,%s)
        """,
        (
            venue_name,
            city,
            country,
        )
    )

    venue_mapping[venue_name] = cursor.lastrowid
    venues_created += 1

print("Venues reused:", venues_reused)
print("Venues created:", venues_created)


# =============================================================================
# SEASON MAPPING
# =============================================================================
#
# Test matches are assigned to their calendar year.
# Player career statistics use a dedicated CAREER season.
# =============================================================================

print()
print("=" * 80)
print("SEASON SETUP")
print("=" * 80)

season_mapping = {}

years_needed = sorted({
    parse_date(row["match_date"]).year
    for row in matches
})

for year in years_needed:
    season_name = str(year)

    row = query_one(
        """
        SELECT id
        FROM seasons
        WHERE name = %s
          AND competition_id = %s
        LIMIT 1
        """,
        (
            season_name,
            competition_id,
        )
    )

    if row:
        season_mapping[year] = row["id"]
        continue

    cursor.execute(
        """
        INSERT INTO seasons
        (name, competition_id, start_year, end_year)
        VALUES (%s,%s,%s,%s)
        """,
        (
            season_name,
            competition_id,
            year,
            year,
        )
    )

    season_mapping[year] = cursor.lastrowid

# Dedicated Test career season.
career_row = query_one(
    """
    SELECT id
    FROM seasons
    WHERE name = 'CAREER'
      AND competition_id = %s
    LIMIT 1
    """,
    (competition_id,)
)

if career_row:
    career_season_id = career_row["id"]
else:
    cursor.execute(
        """
        INSERT INTO seasons
        (name, competition_id, start_year, end_year)
        VALUES ('CAREER', %s, %s, %s)
        """,
        (
            competition_id,
            min(parse_date(row["match_date"]).year for row in matches),
            max(parse_date(row["match_date"]).year for row in matches),
        )
    )

    career_season_id = cursor.lastrowid

print("Competition ID:", competition_id)
print("Calendar seasons:", len(season_mapping))
print("CAREER season ID:", career_season_id)


# =============================================================================
# MATCH IMPORT
# =============================================================================

print()
print("=" * 80)
print("MATCH IMPORT")
print("=" * 80)

match_mapping = {}

matches_created = 0
matches_reused = 0

for row in matches:
    external_id = text(row["match_id"])

    existing = query_one(
        """
        SELECT id
        FROM matches
        WHERE external_id = %s
        LIMIT 1
        """,
        (external_id,)
    )

    if existing:
        match_mapping[external_id] = existing["id"]
        matches_reused += 1
        continue

    gender = normalize_gender(row.get("gender"))

    team1_name = text(row["team1"])
    team2_name = text(row["team2"])

    team1_id = team_mapping.get(
        (team1_name, gender)
    )

    team2_id = team_mapping.get(
        (team2_name, gender)
    )

    if team1_id is None or team2_id is None:
        fail(
            f"Could not resolve teams for match {external_id}:\n"
            f"  {team1_name} / {team2_name} / {gender}"
        )

    winner_name = text(row.get("winner"))
    winner_id = None

    if winner_name:
        winner_id = team_mapping.get(
            (winner_name, gender)
        )

        # Winner may be present in a team mapping derived from the selected
        # match-team rows. If not, resolve it directly from DB.
        if winner_id is None:
            winner_row = query_one(
                """
                SELECT id
                FROM teams
                WHERE name = %s
                  AND gender = %s
                ORDER BY id
                LIMIT 1
                """,
                (
                    winner_name,
                    gender,
                )
            )

            if winner_row:
                winner_id = winner_row["id"]

    venue_name = text(row.get("venue"))
    venue_id = venue_mapping.get(venue_name)

    match_date = parse_date(row["match_date"])

    result_type = (
        text(row.get("result_type"))
        or "COMPLETED"
    ).upper()

    # Existing Match entity uses matchStatus.
    match_status = result_type

    stage = "Test"

    toss_decision = text(row.get("toss_decision"))
    result_description = text(row.get("result_description"))

    # Existing matches table uses winner_team_id and toss_winner_team_id.
    toss_winner_name = text(row.get("toss_winner"))
    toss_winner_id = None

    if toss_winner_name:
        toss_winner_id = team_mapping.get((toss_winner_name, gender))

        if toss_winner_id is None:
            toss_row = query_one(
                """
                SELECT id
                FROM teams
                WHERE name = %s
                  AND gender = %s
                ORDER BY id
                LIMIT 1
                """,
                (
                    toss_winner_name,
                    gender,
                )
            )

            if toss_row:
                toss_winner_id = toss_row["id"]

    cursor.execute(
        """
        INSERT INTO matches
        (
            external_id,
            match_date,
            match_status,
            stage,
            counted_in_standings,
            result_description,
            toss_decision,
            competition_id,
            season_id,
            team1_id,
            team2_id,
            toss_winner_team_id,
            venue_id,
            winner_team_id
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s
        )
        """,
        (
            external_id,
            match_date,
            match_status,
            stage,
            True,
            result_description,
            toss_decision,
            competition_id,
            season_mapping[match_date.year],
            team1_id,
            team2_id,
            toss_winner_id,
            venue_id,
            winner_id,
        )
    )

    match_mapping[external_id] = cursor.lastrowid
    matches_created += 1

print("Matches created:", matches_created)
print("Matches reused:", matches_reused)


# =============================================================================
# MATCH-TEAM STATS
# =============================================================================

print()
print("=" * 80)
print("MATCH-TEAM STATISTICS")
print("=" * 80)

match_team_created = 0
match_team_existing = 0

for row in match_team:
    external_match_id = text(row["match_id"])
    match_id = match_mapping.get(external_match_id)

    if match_id is None:
        fail(
            f"No database match mapping for {external_match_id}"
        )

    gender = normalize_gender(row.get("gender"))
    team_name = text(row["team_name"])

    team_id = team_mapping.get(
        (team_name, gender)
    )

    if team_id is None:
        fail(
            f"No team mapping for {team_name}/{gender}"
        )

    existing = query_one(
        """
        SELECT id
        FROM match_team_stats
        WHERE match_id = %s
          AND team_id = %s
        LIMIT 1
        """,
        (
            match_id,
            team_id,
        )
    )

    if existing:
        match_team_existing += 1
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
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            match_id,
            team_id,
            integer(row["runs"]),
            integer(row["wickets"]),
            integer(row["total_balls"]),
            integer(row["allocated_balls"]),
            integer(row["fours"]),
            integer(row["sixes"]),
            integer(row["extras"]),
            decimal(row["run_rate"]),
        )
    )

    match_team_created += 1

print("Match-team rows created:", match_team_created)
print("Match-team rows already existed:", match_team_existing)


# =============================================================================
# PLAYER-MATCH PERFORMANCE
# =============================================================================

print()
print("=" * 80)
print("PLAYER-MATCH PERFORMANCE")
print("=" * 80)

performance_created = 0
performance_existing = 0

for row in player_match:
    external_match_id = text(row["match_id"])
    external_player_id = text(row["player_external_id"])

    match_id = match_mapping.get(external_match_id)
    player_id = player_mapping.get(external_player_id)

    if match_id is None:
        fail(
            f"No match mapping for {external_match_id}"
        )

    if player_id is None:
        fail(
            f"No player mapping for {external_player_id}"
        )

    existing = query_one(
        """
        SELECT id
        FROM player_match_performance
        WHERE player_id = %s
          AND match_id = %s
        LIMIT 1
        """,
        (
            player_id,
            match_id,
        )
    )

    if existing:
        performance_existing += 1
        continue

    gender = normalize_gender(row.get("gender"))
    team_name = text(row.get("team_name"))

    team_id = team_mapping.get(
        (team_name, gender)
    )

    cursor.execute(
        """
        INSERT INTO player_match_performance
        (
            player_id,
            match_id,
            team_id,
            batting_runs,
            balls_faced,
            fours,
            sixes,
            batting_strike_rate,
            not_out,
            batted,
            balls_bowled,
            runs_conceded,
            wickets,
            bowling_economy,
            maidens
        )
        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s
        )
        """,
        (
            player_id,
            match_id,
            team_id,
            integer(row["batting_runs"]),
            integer(row["balls_faced"]),
            integer(row["fours"]),
            integer(row["sixes"]),
            decimal(row["batting_strike_rate"]),
            boolean(row["not_out"]),
            boolean(row["batted"]),
            integer(row["balls_bowled"]),
            integer(row["runs_conceded"]),
            integer(row["wickets"]),
            decimal(row["bowling_economy"]),
            integer(row["maidens"]),
        )
    )

    performance_created += 1

print("Player-match rows created:", performance_created)
print("Player-match rows already existed:", performance_existing)


# =============================================================================
# PLAYER CAREER STATISTICS
# =============================================================================
#
# The Test processor's player_statistics.csv is a Test CAREER aggregation.
# It is therefore stored under:
#
#   competition = International Test
#   season      = CAREER
#   scope       = CAREER
# =============================================================================

print()
print("=" * 80)
print("PLAYER CAREER STATISTICS")
print("=" * 80)

career_created = 0
career_existing = 0

for row in career_selected:
    external_player_id = text(row["player_external_id"])
    player_id = player_mapping.get(external_player_id)

    if player_id is None:
        # A player may be present in the full career CSV but not in the pilot.
        # career_selected prevents this in normal operation.
        continue

    existing = query_one(
        """
        SELECT id
        FROM player_statistics
        WHERE player_id = %s
          AND competition_id = %s
          AND season_id = %s
          AND scope = 'CAREER'
        LIMIT 1
        """,
        (
            player_id,
            competition_id,
            career_season_id,
        )
    )

    if existing:
        career_existing += 1
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
            %s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s
        )
        """,
        (
            player_id,
            competition_id,
            career_season_id,
            "CAREER",
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

    career_created += 1

print("Career rows created:", career_created)
print("Career rows already existed:", career_existing)


# =============================================================================
# COMMIT
# =============================================================================

connection.commit()

print()
print("=" * 80)
print("TEST PILOT IMPORT COMPLETE")
print("=" * 80)

print()
print("BASE ENTITIES")
print(f"  Teams created:                    {teams_created:,}")
print(f"  Players created:                  {players_created:,}")
print(f"  Venues created:                   {venues_created:,}")

print()
print("MATCHES")
print(f"  Matches created:                  {matches_created:,}")
print(f"  Existing matches reused:         {matches_reused:,}")

print()
print("MATCH TEAM STATS")
print(f"  Inserted:                         {match_team_created:,}")
print(f"  Already existed:                  {match_team_existing:,}")

print()
print("PLAYER MATCH PERFORMANCE")
print(f"  Inserted:                         {performance_created:,}")
print(f"  Already existed:                  {performance_existing:,}")

print()
print("PLAYER CAREER STATISTICS")
print(f"  Inserted:                         {career_created:,}")
print(f"  Already existed:                  {career_existing:,}")

print()
print("Transaction committed successfully.")
print("No delete operation was performed.")

cursor.close()
connection.close()

print()
print("MySQL connection closed.")

