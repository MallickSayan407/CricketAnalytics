import csv
from collections import Counter, defaultdict
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"
)

MATCHES_FILE = BASE_DIR / "matches.csv"
MATCH_TEAM_FILE = BASE_DIR / "match_team_stats.csv"
PLAYER_MATCH_FILE = BASE_DIR / "player_match_performance.csv"
PLAYER_STATS_FILE = BASE_DIR / "player_statistics.csv"
TEAMS_FILE = BASE_DIR / "teams.csv"


# ============================================================
# HELPERS
# ============================================================

def read_csv(path):
    with path.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as f:
        return list(csv.DictReader(f))


def integer(value):
    if value in (None, ""):
        return 0

    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0


def number(value):
    if value in (None, ""):
        return 0.0

    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def check(condition, message, failures):
    if condition:
        print(f"[PASS] {message}")
    else:
        print(f"[FAIL] {message}")
        failures.append(message)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 90)
    print("PROCESSED T20 INTERNATIONAL DATASET AUDIT")
    print("=" * 90)

    failures = []

    # --------------------------------------------------------
    # File existence
    # --------------------------------------------------------

    files = [
        MATCHES_FILE,
        MATCH_TEAM_FILE,
        PLAYER_MATCH_FILE,
        PLAYER_STATS_FILE,
        TEAMS_FILE,
    ]

    print("\n" + "=" * 90)
    print("FILE CHECK")
    print("=" * 90)

    for path in files:

        check(
            path.exists(),
            f"{path.name} exists",
            failures
        )

    if failures:
        print("\nRequired files are missing. Stopping.")
        return

    # --------------------------------------------------------
    # Read files
    # --------------------------------------------------------

    matches = read_csv(MATCHES_FILE)
    match_teams = read_csv(MATCH_TEAM_FILE)
    player_matches = read_csv(PLAYER_MATCH_FILE)
    player_stats = read_csv(PLAYER_STATS_FILE)
    teams = read_csv(TEAMS_FILE)

    # ========================================================
    # BASIC COUNTS
    # ========================================================

    print("\n" + "=" * 90)
    print("ROW COUNTS")
    print("=" * 90)

    print(f"\nMatches:              {len(matches):,}")
    print(f"Match-team rows:      {len(match_teams):,}")
    print(f"Player-match rows:    {len(player_matches):,}")
    print(f"Career player rows:   {len(player_stats):,}")
    print(f"Teams:                {len(teams):,}")

    check(
        len(matches) == 5700,
        "Exactly 5,700 matches",
        failures
    )

    check(
        len(match_teams) == 11400,
        "Exactly 11,400 match-team rows",
        failures
    )

    # ========================================================
    # MATCH UNIQUENESS
    # ========================================================

    print("\n" + "=" * 90)
    print("MATCH UNIQUENESS")
    print("=" * 90)

    match_ids = [
        row["match_id"]
        for row in matches
    ]

    match_id_counter = Counter(match_ids)

    duplicate_matches = [
        (match_id, count)
        for match_id, count in match_id_counter.items()
        if count > 1
    ]

    print(
        f"\nUnique match IDs: "
        f"{len(set(match_ids)):,}"
    )

    print(
        f"Duplicate match IDs: "
        f"{len(duplicate_matches):,}"
    )

    check(
        len(match_ids) == len(set(match_ids)),
        "No duplicate match IDs",
        failures
    )

    # ========================================================
    # MATCH STATUS / RESULT
    # ========================================================

    print("\n" + "=" * 90)
    print("MATCH STATUS / RESULT")
    print("=" * 90)

    status_counter = Counter(
        row["result_type"]
        for row in matches
    )

    for key, value in status_counter.items():
        print(f"{key}: {value}")

    check(
        status_counter["WINNER"] == 5536,
        "Winner results = 5,536",
        failures
    )

    check(
        status_counter["TIED"] == 51,
        "Tied results = 51",
        failures
    )

    check(
        status_counter["NO_RESULT"] == 113,
        "No-result matches = 113",
        failures
    )

    # ========================================================
    # GENDER
    # ========================================================

    print("\n" + "=" * 90)
    print("GENDER")
    print("=" * 90)

    gender_counter = Counter(
        row["gender"]
        for row in matches
    )

    for key, value in gender_counter.items():
        print(f"{key}: {value}")

    check(
        gender_counter["male"] == 3539,
        "Male matches = 3,539",
        failures
    )

    check(
        gender_counter["female"] == 2161,
        "Female matches = 2,161",
        failures
    )

    # ========================================================
    # MATCH TEAM UNIQUENESS
    # ========================================================

    print("\n" + "=" * 90)
    print("MATCH-TEAM UNIQUENESS")
    print("=" * 90)

    match_team_keys = [
        (
            row["match_id"],
            row["team_name"],
            row["gender"]
        )
        for row in match_teams
    ]

    duplicate_match_team = [
        (key, count)
        for key, count in Counter(
            match_team_keys
        ).items()
        if count > 1
    ]

    print(
        f"\nUnique match-team keys: "
        f"{len(set(match_team_keys)):,}"
    )

    print(
        f"Duplicate match-team keys: "
        f"{len(duplicate_match_team):,}"
    )

    check(
        len(match_team_keys)
        == len(set(match_team_keys)),
        "No duplicate match-team rows",
        failures
    )

    # ========================================================
    # EXACTLY TWO TEAMS PER MATCH
    # ========================================================

    teams_per_match = defaultdict(list)

    for row in match_teams:

        teams_per_match[
            row["match_id"]
        ].append(row)

    bad_team_counts = {
        match_id: len(rows)
        for match_id, rows in teams_per_match.items()
        if len(rows) != 2
    }

    print(
        f"\nMatches with exactly 2 team rows: "
        f"{len(matches) - len(bad_team_counts):,}"
    )

    print(
        f"Matches with incorrect team-row count: "
        f"{len(bad_team_counts):,}"
    )

    check(
        len(bad_team_counts) == 0,
        "Every match has exactly 2 match-team rows",
        failures
    )

    # ========================================================
    # PLAYER-MATCH UNIQUENESS
    # ========================================================

    print("\n" + "=" * 90)
    print("PLAYER-MATCH UNIQUENESS")
    print("=" * 90)

    player_match_keys = [
        (
            row["match_id"],
            row["player_external_id"]
        )
        for row in player_matches
    ]

    duplicate_player_matches = [
        (key, count)
        for key, count in Counter(
            player_match_keys
        ).items()
        if count > 1
    ]

    print(
        f"\nUnique player-match keys: "
        f"{len(set(player_match_keys)):,}"
    )

    print(
        f"Duplicate player-match rows: "
        f"{len(duplicate_player_matches):,}"
    )

    check(
        len(player_match_keys)
        == len(set(player_match_keys)),
        "No duplicate player-match rows",
        failures
    )

    # ========================================================
    # PLAYER REFERENCES
    # ========================================================

    print("\n" + "=" * 90)
    print("PLAYER REFERENCES")
    print("=" * 90)

    missing_external_ids = [
        row
        for row in player_matches
        if not row["player_external_id"]
    ]

    missing_player_names = [
        row
        for row in player_matches
        if not row["player_name"]
    ]

    check(
        len(missing_external_ids) == 0,
        "Every player-match row has a player external ID",
        failures
    )

    check(
        len(missing_player_names) == 0,
        "Every player-match row has a player name",
        failures
    )

    # ========================================================
    # MATCH REFERENCES
    # ========================================================

    match_id_set = set(match_ids)

    orphan_match_team_rows = [
        row
        for row in match_teams
        if row["match_id"] not in match_id_set
    ]

    orphan_player_match_rows = [
        row
        for row in player_matches
        if row["match_id"] not in match_id_set
    ]

    check(
        len(orphan_match_team_rows) == 0,
        "All match-team rows reference an existing match",
        failures
    )

    check(
        len(orphan_player_match_rows) == 0,
        "All player-match rows reference an existing match",
        failures
    )

    # ========================================================
    # TEAM REFERENCES
    # ========================================================

    team_keys = {
        (
            row["team_name"],
            row["gender"]
        )
        for row in teams
    }

    orphan_match_team_teams = [
        row
        for row in match_teams
        if (
            row["team_name"],
            row["gender"]
        ) not in team_keys
    ]

    orphan_player_teams = [
        row
        for row in player_matches
        if (
            row["team_name"],
            row["gender"]
        ) not in team_keys
    ]

    check(
        len(orphan_match_team_teams) == 0,
        "All match-team teams exist in teams.csv",
        failures
    )

    check(
        len(orphan_player_teams) == 0,
        "All player teams exist in teams.csv",
        failures
    )

    # ========================================================
    # BASIC STAT VALIDATION
    # ========================================================

    print("\n" + "=" * 90)
    print("STAT VALIDATION")
    print("=" * 90)

    numeric_player_fields = [
        "batting_runs",
        "balls_faced",
        "fours",
        "sixes",
        "balls_bowled",
        "runs_conceded",
        "wickets",
        "maidens",
    ]

    negative_player_values = []

    for row in player_matches:

        for field in numeric_player_fields:

            if integer(row[field]) < 0:

                negative_player_values.append(
                    (
                        row["match_id"],
                        row["player_name"],
                        field,
                        row[field]
                    )
                )

    check(
        len(negative_player_values) == 0,
        "No negative player statistics",
        failures
    )

    numeric_team_fields = [
        "runs",
        "wickets",
        "total_balls",
        "allocated_balls",
        "fours",
        "sixes",
        "extras",
    ]

    negative_team_values = []

    for row in match_teams:

        for field in numeric_team_fields:

            if integer(row[field]) < 0:

                negative_team_values.append(
                    (
                        row["match_id"],
                        row["team_name"],
                        field,
                        row[field]
                    )
                )

    check(
        len(negative_team_values) == 0,
        "No negative team statistics",
        failures
    )

    # ========================================================
    # FOURS / SIXES PLAUSIBILITY
    # ========================================================

    impossible_fours = []

    for row in player_matches:

        if (
            integer(row["fours"]) * 4
            > integer(row["batting_runs"])
        ):

            impossible_fours.append(row)

    impossible_sixes = []

    for row in player_matches:

        if (
            integer(row["sixes"]) * 6
            > integer(row["batting_runs"])
        ):

            impossible_sixes.append(row)

    check(
        len(impossible_fours) == 0,
        "No player has impossible four counts",
        failures
    )

    check(
        len(impossible_sixes) == 0,
        "No player has impossible six counts",
        failures
    )

    # ========================================================
    # TEAM RUNS VS PLAYER RUNS
    # ========================================================

    print("\n" + "=" * 90)
    print("RUN RECONCILIATION")
    print("=" * 90)

    total_team_runs = sum(
        integer(row["runs"])
        for row in match_teams
    )

    total_player_runs = sum(
        integer(row["batting_runs"])
        for row in player_matches
    )

    total_team_extras = sum(
        integer(row["extras"])
        for row in match_teams
    )

    print(
        f"\nTeam runs:              "
        f"{total_team_runs:,}"
    )

    print(
        f"Player batting runs:    "
        f"{total_player_runs:,}"
    )

    print(
        f"Team extras:            "
        f"{total_team_extras:,}"
    )

    print(
        f"Player + extras:        "
        f"{total_player_runs + total_team_extras:,}"
    )

    run_difference = (
        total_team_runs
        - total_player_runs
        - total_team_extras
    )

    print(
        f"Reconciliation difference: "
        f"{run_difference:,}"
    )

    check(
        run_difference == 0,
        "Team runs = player runs + extras",
        failures
    )

    # ========================================================
    # TEAM FOUR / SIX RECONCILIATION
    # ========================================================

    total_team_fours = sum(
        integer(row["fours"])
        for row in match_teams
    )

    total_player_fours = sum(
        integer(row["fours"])
        for row in player_matches
    )

    total_team_sixes = sum(
        integer(row["sixes"])
        for row in match_teams
    )

    total_player_sixes = sum(
        integer(row["sixes"])
        for row in player_matches
    )

    print(
        f"\nTeam fours:             "
        f"{total_team_fours:,}"
    )

    print(
        f"Player fours:           "
        f"{total_player_fours:,}"
    )

    print(
        f"Team sixes:             "
        f"{total_team_sixes:,}"
    )

    print(
        f"Player sixes:           "
        f"{total_player_sixes:,}"
    )

    check(
        total_team_fours == total_player_fours,
        "Team fours reconcile with player fours",
        failures
    )

    check(
        total_team_sixes == total_player_sixes,
        "Team sixes reconcile with player sixes",
        failures
    )

    # ========================================================
    # WICKET RECONCILIATION
    # ========================================================

    total_team_wickets = sum(
        integer(row["wickets"])
        for row in match_teams
    )

    total_bowler_wickets = sum(
        integer(row["wickets"])
        for row in player_matches
    )

    print(
        f"\nTeam wickets:           "
        f"{total_team_wickets:,}"
    )

    print(
        f"Bowler wickets:         "
        f"{total_bowler_wickets:,}"
    )

    # Some wickets are not credited to bowlers, so the bowler
    # total should never exceed the team total.
    check(
        total_bowler_wickets <= total_team_wickets,
        "Bowler wickets do not exceed team wickets",
        failures
    )

    # ========================================================
    # CAREER PLAYER UNIQUENESS
    # ========================================================

    print("\n" + "=" * 90)
    print("CAREER STATISTICS")
    print("=" * 90)

    career_keys = [
        (
            row["player_external_id"],
            row["gender"]
        )
        for row in player_stats
    ]

    duplicate_career_keys = [
        (key, count)
        for key, count in Counter(
            career_keys
        ).items()
        if count > 1
    ]

    print(
        f"\nUnique career keys: "
        f"{len(set(career_keys)):,}"
    )

    print(
        f"Duplicate career keys: "
        f"{len(duplicate_career_keys):,}"
    )

    check(
        len(career_keys)
        == len(set(career_keys)),
        "No duplicate career player keys",
        failures
    )

    # ========================================================
    # CAREER AGGREGATION RECONCILIATION
    # ========================================================

    print("\n" + "=" * 90)
    print("CAREER AGGREGATION RECONCILIATION")
    print("=" * 90)

    # Aggregate player-match rows ourselves.

    expected = {}

    for row in player_matches:

        key = (
            row["player_external_id"],
            row["gender"]
        )

        if key not in expected:

            expected[key] = {
                "matches": 0,
                "batting_innings": 0,
                "runs": 0,
                "balls_faced": 0,
                "fours": 0,
                "sixes": 0,
                "not_outs": 0,
                "wickets": 0,
                "balls_bowled": 0,
                "runs_conceded": 0,
                "five_wicket_hauls": 0,
                "centuries": 0,
                "fifties": 0,
            }

        e = expected[key]

        e["matches"] += 1

        if row["batted"].lower() == "true":

            e["batting_innings"] += 1

        e["runs"] += integer(
            row["batting_runs"]
        )

        e["balls_faced"] += integer(
            row["balls_faced"]
        )

        e["fours"] += integer(
            row["fours"]
        )

        e["sixes"] += integer(
            row["sixes"]
        )

        if row["not_out"].lower() == "true":

            e["not_outs"] += 1

        e["wickets"] += integer(
            row["wickets"]
        )

        e["balls_bowled"] += integer(
            row["balls_bowled"]
        )

        e["runs_conceded"] += integer(
            row["runs_conceded"]
        )

        wickets = integer(
            row["wickets"]
        )

        if wickets >= 5:

            e["five_wicket_hauls"] += 1

        runs = integer(
            row["batting_runs"]
        )

        if runs >= 100:

            e["centuries"] += 1

        elif runs >= 50:

            e["fifties"] += 1

    career_mismatches = []

    processed_career_keys = set()

    for row in player_stats:

        key = (
            row["player_external_id"],
            row["gender"]
        )

        processed_career_keys.add(key)

        if key not in expected:

            career_mismatches.append(
                (
                    key,
                    "career row has no player-match rows"
                )
            )

            continue

        e = expected[key]

        checks_to_compare = [
            ("matches", "matches"),
            ("batting_innings", "batting_innings"),
            ("runs", "runs"),
            ("balls_faced", "balls_faced"),
            ("fours", "fours"),
            ("sixes", "sixes"),
            ("not_outs", "not_outs"),
            ("wickets", "wickets"),
            ("balls_bowled", "balls_bowled"),
            ("runs_conceded", "runs_conceded"),
            ("five_wicket_hauls", "five_wicket_hauls"),
            ("centuries", "centuries"),
            ("fifties", "fifties"),
        ]

        for csv_field, expected_field in checks_to_compare:

            actual = integer(
                row[csv_field]
            )

            expected_value = e[
                expected_field
            ]

            if actual != expected_value:

                career_mismatches.append(
                    (
                        key,
                        csv_field,
                        actual,
                        expected_value
                    )
                )

    missing_career_rows = (
        set(expected.keys())
        - processed_career_keys
    )

    print(
        f"\nPlayer-match career keys: "
        f"{len(expected):,}"
    )

    print(
        f"Processed career keys:     "
        f"{len(processed_career_keys):,}"
    )

    print(
        f"Career mismatches:          "
        f"{len(career_mismatches):,}"
    )

    print(
        f"Missing career rows:        "
        f"{len(missing_career_rows):,}"
    )

    check(
        len(career_mismatches) == 0,
        "Career statistics reconcile with player-match data",
        failures
    )

    check(
        len(missing_career_rows) == 0,
        "Every player-match career key has a career row",
        failures
    )

    # ========================================================
    # GENDER CAREER RECONCILIATION
    # ========================================================

    career_gender = Counter(
        row["gender"]
        for row in player_stats
    )

    player_match_gender = Counter(
        (
            row["player_external_id"],
            row["gender"]
        )
        for row in player_matches
    )

    print("\nCareer player rows by gender:")

    for gender, count in career_gender.items():

        print(
            f"{gender}: {count:,}"
        )

    check(
        set(
            career_gender.keys()
        ).issubset(
            {"male", "female"}
        ),
        "Career statistics contain only male/female genders",
        failures
    )

    # ========================================================
    # SUPER OVER PROTECTION CHECK
    # ========================================================

    print("\n" + "=" * 90)
    print("SUPER OVER PROTECTION")
    print("=" * 90)

    # The processed data contains no explicit super-over flag,
    # so validate against the known regulation totals from the
    # raw dataset audit.

    check(
        total_team_runs == 1409779,
        "Processed team runs equal 1,409,779 regulation runs",
        failures
    )

    check(
        total_player_runs + total_team_extras
        == 1409779,
        "Processed player runs + extras equal regulation runs",
        failures
    )

    # ========================================================
    # TOP PLAYERS
    # ========================================================

    print("\n" + "=" * 90)
    print("TOP 10 T20I RUN SCORERS")
    print("=" * 90)

    top_runs = sorted(
        player_stats,
        key=lambda row: integer(
            row["runs"]
        ),
        reverse=True
    )

    for index, row in enumerate(
        top_runs[:10],
        start=1
    ):

        print(
            f"{index:2}. "
            f"{row['player_name']:<30} "
            f"{row['gender']:<7} "
            f"matches={integer(row['matches']):>3} "
            f"runs={integer(row['runs']):>5} "
            f"100s={integer(row['centuries']):>2} "
            f"50s={integer(row['fifties']):>2}"
        )

    print("\n" + "=" * 90)
    print("TOP 10 T20I WICKET TAKERS")
    print("=" * 90)

    top_wickets = sorted(
        player_stats,
        key=lambda row: integer(
            row["wickets"]
        ),
        reverse=True
    )

    for index, row in enumerate(
        top_wickets[:10],
        start=1
    ):

        print(
            f"{index:2}. "
            f"{row['player_name']:<30} "
            f"{row['gender']:<7} "
            f"matches={integer(row['matches']):>3} "
            f"wickets={integer(row['wickets']):>3} "
            f"econ={number(row['economy']):>5.2f}"
        )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    print("\n" + "=" * 90)
    print("FINAL AUDIT RESULT")
    print("=" * 90)

    if failures:

        print(
            f"\nT20I PROCESSED DATASET AUDIT: FAIL"
        )

        print(
            f"\nFailures: {len(failures)}"
        )

        for failure in failures:

            print(
                f" - {failure}"
            )

    else:

        print(
            "\nT20I PROCESSED DATASET AUDIT: PASS"
        )

    print("=" * 90)


if __name__ == "__main__":
    main()