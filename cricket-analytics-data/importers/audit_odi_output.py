import csv
from collections import Counter, defaultdict
from pathlib import Path


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = (
    BASE_DIR
    / "processed"
    / "odi"
)


MATCHES_FILE = OUTPUT_DIR / "matches.csv"
MATCH_TEAM_FILE = OUTPUT_DIR / "match_team_stats.csv"
PLAYER_MATCH_FILE = OUTPUT_DIR / "player_match_performance.csv"
PLAYER_STATS_FILE = OUTPUT_DIR / "player_statistics.csv"


# =============================================================================
# HELPERS
# =============================================================================

def read_csv(filepath):
    with filepath.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        return list(
            csv.DictReader(file)
        )


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def print_section(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# =============================================================================
# MAIN AUDIT
# =============================================================================

def main():

    print("=" * 80)
    print("ODI PROCESSED DATA QUALITY AUDIT")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # FILE EXISTENCE
    # -------------------------------------------------------------------------

    required_files = [
        MATCHES_FILE,
        MATCH_TEAM_FILE,
        PLAYER_MATCH_FILE,
        PLAYER_STATS_FILE,
    ]

    missing_files = [
        str(path)
        for path in required_files
        if not path.exists()
    ]

    if missing_files:

        print()
        print("ERROR: Missing required files:")

        for file in missing_files:
            print(f"  {file}")

        return

    # -------------------------------------------------------------------------
    # LOAD DATA
    # -------------------------------------------------------------------------

    matches = read_csv(
        MATCHES_FILE
    )

    match_team_stats = read_csv(
        MATCH_TEAM_FILE
    )

    player_match = read_csv(
        PLAYER_MATCH_FILE
    )

    player_stats = read_csv(
        PLAYER_STATS_FILE
    )

    print()
    print("Loaded records:")

    print(
        f"  Matches:              {len(matches)}"
    )

    print(
        f"  Match-team records:   {len(match_team_stats)}"
    )

    print(
        f"  Player-match records: {len(player_match)}"
    )

    print(
        f"  Player statistics:    {len(player_stats)}"
    )

    # =========================================================================
    # 1. DUPLICATE CHECKS
    # =========================================================================

    print_section(
        "1. DUPLICATE CHECKS"
    )

    match_ids = [
        row["match_id"]
        for row in matches
    ]

    duplicate_match_ids = [
        match_id
        for match_id, count in Counter(
            match_ids
        ).items()
        if count > 1
    ]

    print(
        f"Duplicate match IDs: {len(duplicate_match_ids)}"
    )

    # -------------------------------------------------------------------------
    # MATCH-TEAM DUPLICATES
    # -------------------------------------------------------------------------

    match_team_keys = [
        (
            row["match_id"],
            row["team_id"]
        )
        for row in match_team_stats
    ]

    duplicate_match_team_keys = [
        key
        for key, count in Counter(
            match_team_keys
        ).items()
        if count > 1
    ]

    print(
        "Duplicate match-team records: "
        f"{len(duplicate_match_team_keys)}"
    )

    # -------------------------------------------------------------------------
    # PLAYER-MATCH DUPLICATES
    # -------------------------------------------------------------------------

    player_match_keys = [
        (
            row["match_id"],
            row["player_id"],
            row["team_id"]
        )
        for row in player_match
    ]

    duplicate_player_match_keys = [
        key
        for key, count in Counter(
            player_match_keys
        ).items()
        if count > 1
    ]

    print(
        "Duplicate player-match records: "
        f"{len(duplicate_player_match_keys)}"
    )

    # =========================================================================
    # 2. TEAM TOTAL CHECKS
    # =========================================================================

    print_section(
        "2. TEAM TOTAL CHECKS"
    )

    invalid_team_stats = []

    for row in match_team_stats:

        wickets = to_int(
            row["wickets"]
        )

        runs = to_int(
            row["runs"]
        )

        balls = to_int(
            row["total_balls"]
        )

        fours = to_int(
            row["fours"]
        )

        sixes = to_int(
            row["sixes"]
        )

        if wickets > 10:

            invalid_team_stats.append(
                (
                    row["match_id"],
                    row["team_name"],
                    "invalid wickets"
                )
            )

        if wickets < 0:

            invalid_team_stats.append(
                (
                    row["match_id"],
                    row["team_name"],
                    "negative wickets"
                )
            )

        if runs < 0:

            invalid_team_stats.append(
                (
                    row["match_id"],
                    row["team_name"],
                    "negative runs"
                )
            )

        if balls < 0:

            invalid_team_stats.append(
                (
                    row["match_id"],
                    row["team_name"],
                    "negative balls"
                )
            )

        if fours < 0 or sixes < 0:

            invalid_team_stats.append(
                (
                    row["match_id"],
                    row["team_name"],
                    "negative boundaries"
                )
            )

    print(
        f"Invalid team-stat records: "
        f"{len(invalid_team_stats)}"
    )

    if invalid_team_stats:

        print()
        print("First 10 errors:")

        for match_id, team_name, reason in (
            invalid_team_stats[:10]
        ):

            print(
                f"{match_id} "
                f"{team_name} "
                f"{reason}"
            )

    # =========================================================================
    # 3. PLAYER-MATCH CHECKS
    # =========================================================================

    print_section(
        "3. PLAYER-MATCH CHECKS"
    )

    invalid_player_match = []

    for row in player_match:

        batting_runs = to_int(
            row["batting_runs"]
        )

        balls_faced = to_int(
            row["balls_faced"]
        )

        balls_bowled = to_int(
            row["balls_bowled"]
        )

        runs_conceded = to_int(
            row["runs_conceded"]
        )

        wickets = to_int(
            row["wickets"]
        )

        fours = to_int(
            row["fours"]
        )

        sixes = to_int(
            row["sixes"]
        )

        batted = (
            str(row.get("batted", ""))
            .lower()
            == "true"
        )

        not_out = (
            str(row.get("not_out", ""))
            .lower()
            == "true"
        )

        if batting_runs < 0:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "negative batting runs"
                )
            )

        if balls_faced < 0:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "negative balls faced"
                )
            )

        if balls_bowled < 0:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "negative balls bowled"
                )
            )

        if runs_conceded < 0:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "negative runs conceded"
                )
            )

        if wickets < 0 or wickets > 10:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "invalid wickets"
                )
            )

        if fours < 0 or sixes < 0:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "negative boundaries"
                )
            )

        if not batted and not_out:

            invalid_player_match.append(
                (
                    row["match_id"],
                    row["player_name"],
                    "non-batter marked not out"
                )
            )

    print(
        f"Invalid player-match records: "
        f"{len(invalid_player_match)}"
    )

    if invalid_player_match:

        print()
        print("First 10 errors:")

        for match_id, player_name, reason in (
            invalid_player_match[:10]
        ):

            print(
                f"{match_id} "
                f"{player_name} "
                f"{reason}"
            )

    # =========================================================================
    # 4. PLAYER AGGREGATE CHECKS
    # =========================================================================

    print_section(
        "4. PLAYER AGGREGATE CHECKS"
    )

    invalid_aggregates = []

    for row in player_stats:

        matches_count = to_int(
            row["matches"]
        )

        batting_innings = to_int(
            row["batting_innings"]
        )

        runs = to_int(
            row["runs"]
        )

        balls_faced = to_int(
            row["balls_faced"]
        )

        not_outs = to_int(
            row["not_outs"]
        )

        wickets = to_int(
            row["wickets"]
        )

        balls_bowled = to_int(
            row["balls_bowled"]
        )

        runs_conceded = to_int(
            row["runs_conceded"]
        )

        if batting_innings > matches_count:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "batting innings > matches"
                )
            )

        if not_outs > batting_innings:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "not outs > batting innings"
                )
            )

        if runs < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative runs"
                )
            )

        if balls_faced < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative balls faced"
                )
            )

        if wickets < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative wickets"
                )
            )

        if balls_bowled < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative balls bowled"
                )
            )

        if runs_conceded < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative runs conceded"
                )
            )

        if to_int(row["fifties"]) < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative fifties"
                )
            )

        if to_int(row["centuries"]) < 0:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "negative centuries"
                )
            )

        if to_int(row["best_bowling_wickets"]) > 10:

            invalid_aggregates.append(
                (
                    row["player_name"],
                    "best bowling wickets > 10"
                )
            )

    print(
        f"Invalid aggregate records: "
        f"{len(invalid_aggregates)}"
    )

    if invalid_aggregates:

        print()
        print("First 10 errors:")

        for player_name, reason in (
            invalid_aggregates[:10]
        ):

            print(
                f"{player_name}: {reason}"
            )

    # =========================================================================
    # 5. GENDER CHECK
    # =========================================================================

    print_section(
        "5. GENDER CHECK"
    )

    match_gender_counts = Counter(
        row["gender"]
        for row in matches
    )

    player_gender_counts = Counter(
        row["gender"]
        for row in player_match
    )

    print("Matches:")

    for gender, count in sorted(
        match_gender_counts.items()
    ):

        print(
            f"  {gender}: {count}"
        )

    print()
    print("Player performances:")

    for gender, count in sorted(
        player_gender_counts.items()
    ):

        print(
            f"  {gender}: {count}"
        )

    # =========================================================================
    # 6. KNOWN PLAYER CHECK
    # =========================================================================

    print_section(
        "6. KNOWN PLAYER CHECK"
    )

    kohli_rows = [
        row
        for row in player_stats
        if row["player_name"].lower()
        == "virat kohli"
        and row["gender"].lower()
        == "male"
    ]

    if not kohli_rows:

        print()
        print(
            "V Kohli aggregate: NOT FOUND"
        )

    else:

        kohli = kohli_rows[0]

        print()
        print("V Kohli aggregate:")

        fields = [
            "matches",
            "batting_innings",
            "runs",
            "balls_faced",
            "highest_score",
            "not_outs",
            "fifties",
            "centuries",
            "batting_average",
            "strike_rate",
            "wickets",
            "economy",
            "bowling_average",
        ]

        for field in fields:

            print(
                f"  {field:<24}: "
                f"{kohli[field]}"
            )

    # =========================================================================
    # 7. MATCH-TEAM CONSISTENCY
    # =========================================================================

    print_section(
        "7. MATCH TEAM CONSISTENCY"
    )

    match_team_count = Counter(
        row["match_id"]
        for row in match_team_stats
    )

    abnormal_matches = {
        match_id: count
        for match_id, count in match_team_count.items()
        if count != 2
    }

    print(
        "Matches without exactly 2 "
        "team-stat records: "
        f"{len(abnormal_matches)}"
    )

    for match_id, count in list(
        sorted(abnormal_matches.items())
    )[:20]:

        print(
            f"  {match_id}: {count} teams"
        )

    # =========================================================================
    # 8. MATCH TOTAL CONSISTENCY
    # =========================================================================

    print_section(
        "8. MATCH TOTAL CONSISTENCY"
    )

    match_team_grouped = defaultdict(
        list
    )

    for row in match_team_stats:

        match_team_grouped[
            row["match_id"]
        ].append(row)

    invalid_match_totals = []

    for match_id, rows in (
        match_team_grouped.items()
    ):

        match_runs = sum(
            to_int(row["runs"])
            for row in rows
        )

        if match_runs < 0:

            invalid_match_totals.append(
                (
                    match_id,
                    match_runs
                )
            )

    print(
        "Invalid match totals: "
        f"{len(invalid_match_totals)}"
    )

    # =========================================================================
    # 9. SUMMARY
    # =========================================================================

    print_section(
        "AUDIT SUMMARY"
    )

    duplicate_total = (
        len(duplicate_match_ids)
        + len(duplicate_match_team_keys)
        + len(duplicate_player_match_keys)
    )

    total_errors = (
        len(invalid_team_stats)
        + len(invalid_player_match)
        + len(invalid_aggregates)
        + len(invalid_match_totals)
        + duplicate_total
    )

    if total_errors == 0:

        print()
        print(
            "STATUS: PASS"
        )

        print()
        print(
            "No structural/statistical errors "
            "were detected by this audit."
        )

    else:

        print()
        print(
            "STATUS: REVIEW REQUIRED"
        )

        print()
        print(
            f"Total detected errors: {total_errors}"
        )

    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()