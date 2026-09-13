import csv
import os
from collections import Counter


BASE_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\ipl"


def read_csv(filename):
    path = os.path.join(BASE_DIR, filename)

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def duplicate_count(rows, keys):

    seen = set()
    duplicates = 0

    for row in rows:

        key = tuple(
            row.get(k, "")
            for k in keys
        )

        if key in seen:
            duplicates += 1
        else:
            seen.add(key)

    return duplicates


def to_int(value):
    try:
        return int(value)
    except:
        return 0


def main():

    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL PROCESSED CSV AUDIT")
    print("=" * 80)

    matches = read_csv("matches.csv")
    teams = read_csv("teams.csv")
    players = read_csv("players.csv")
    match_team = read_csv("match_team_stats.csv")
    performances = read_csv(
        "player_match_performance.csv"
    )
    statistics = read_csv(
        "player_statistics.csv"
    )

    print()
    print("ROW COUNTS")
    print("-" * 80)

    print(f"matches.csv:                    {len(matches)}")
    print(f"teams.csv:                      {len(teams)}")
    print(f"players.csv:                    {len(players)}")
    print(
        f"match_team_stats.csv:           "
        f"{len(match_team)}"
    )
    print(
        f"player_match_performance.csv:   "
        f"{len(performances)}"
    )
    print(
        f"player_statistics.csv:          "
        f"{len(statistics)}"
    )

    # ========================================================================
    # MATCH AUDIT
    # ========================================================================

    print()
    print("MATCH AUDIT")
    print("-" * 80)

    duplicate_matches = duplicate_count(
        matches,
        ["match_id"]
    )

    print(
        f"Duplicate match IDs:             "
        f"{duplicate_matches}"
    )

    match_ids = {
        row["match_id"]
        for row in matches
    }

    print(
        f"Unique match IDs:                "
        f"{len(match_ids)}"
    )

    seasons = Counter(
        row["season"]
        for row in matches
    )

    print()
    print("Seasons:")

    for season, count in sorted(
        seasons.items()
    ):
        print(
            f"  {season}: {count}"
        )

    statuses = Counter(
        row["match_status"]
        for row in matches
    )

    print()
    print("Match statuses:")

    for status, count in statuses.items():
        print(
            f"  {status}: {count}"
        )

    result_types = Counter(
        row["result_type"]
        for row in matches
    )

    print()
    print("Result types:")

    for result_type, count in result_types.items():
        print(
            f"  {result_type}: {count}"
        )

    # ========================================================================
    # TEAM AUDIT
    # ========================================================================

    print()
    print("TEAM AUDIT")
    print("-" * 80)

    team_names = {
        row["team_name"]
        for row in teams
    }

    print(
        f"Canonical teams:                 "
        f"{len(team_names)}"
    )

    print()

    for team in sorted(team_names):
        print(
            f"  {team}"
        )

    duplicate_teams = duplicate_count(
        teams,
        ["team_name"]
    )

    print()
    print(
        f"Duplicate canonical teams:       "
        f"{duplicate_teams}"
    )

    # ========================================================================
    # PLAYER AUDIT
    # ========================================================================

    print()
    print("PLAYER AUDIT")
    print("-" * 80)

    duplicate_players = duplicate_count(
        players,
        ["player_external_id"]
    )

    print(
        f"Duplicate player IDs:             "
        f"{duplicate_players}"
    )

    missing_player_ids = [
        row
        for row in players
        if not row["player_external_id"]
    ]

    print(
        f"Players without external ID:     "
        f"{len(missing_player_ids)}"
    )

    # ========================================================================
    # MATCH-TEAM AUDIT
    # ========================================================================

    print()
    print("MATCH-TEAM AUDIT")
    print("-" * 80)

    duplicate_match_team = duplicate_count(
        match_team,
        [
            "match_id",
            "team_name"
        ]
    )

    print(
        f"Duplicate match-team rows:        "
        f"{duplicate_match_team}"
    )

    invalid_team_rows = [
        row
        for row in match_team
        if row["team_name"] not in team_names
    ]

    print(
        f"Unknown team references:          "
        f"{len(invalid_team_rows)}"
    )

    invalid_runs = [
        row
        for row in match_team
        if to_int(row["runs"]) < 0
    ]

    invalid_wickets = [
        row
        for row in match_team
        if to_int(row["wickets"]) < 0
    ]

    print(
        f"Negative team runs:               "
        f"{len(invalid_runs)}"
    )

    print(
        f"Negative team wickets:            "
        f"{len(invalid_wickets)}"
    )

    # ========================================================================
    # PLAYER PERFORMANCE AUDIT
    # ========================================================================

    print()
    print("PLAYER-MATCH PERFORMANCE AUDIT")
    print("-" * 80)

    duplicate_performances = duplicate_count(
        performances,
        [
            "player_external_id",
            "match_id"
        ]
    )

    print(
        f"Duplicate player-match rows:      "
        f"{duplicate_performances}"
    )

    missing_performance_ids = [
        row
        for row in performances
        if not row["player_external_id"]
    ]

    print(
        f"Missing player external IDs:      "
        f"{len(missing_performance_ids)}"
    )

    performance_unknown_matches = [
        row
        for row in performances
        if row["match_id"] not in match_ids
    ]

    print(
        f"Unknown match references:         "
        f"{len(performance_unknown_matches)}"
    )

    performance_unknown_teams = [
        row
        for row in performances
        if row["team_name"] not in team_names
    ]

    print(
        f"Unknown team references:          "
        f"{len(performance_unknown_teams)}"
    )

    invalid_batting = [
        row
        for row in performances
        if (
            to_int(row["batting_runs"]) < 0
            or to_int(row["balls_faced"]) < 0
            or to_int(row["fours"]) < 0
            or to_int(row["sixes"]) < 0
        )
    ]

    print(
        f"Invalid batting values:           "
        f"{len(invalid_batting)}"
    )

    invalid_bowling = [
        row
        for row in performances
        if (
            to_int(row["balls_bowled"]) < 0
            or to_int(row["runs_conceded"]) < 0
            or to_int(row["wickets"]) < 0
            or to_int(row["maidens"]) < 0
        )
    ]

    print(
        f"Invalid bowling values:           "
        f"{len(invalid_bowling)}"
    )

    # ========================================================================
    # PLAYER STATISTICS AUDIT
    # ========================================================================

    print()
    print("PLAYER STATISTICS AUDIT")
    print("-" * 80)

    duplicate_statistics = duplicate_count(
        statistics,
        [
            "player_external_id",
            "season"
        ]
    )

    print(
        f"Duplicate player-season rows:     "
        f"{duplicate_statistics}"
    )

    invalid_statistics = [
        row
        for row in statistics
        if (
            to_int(row["runs"]) < 0
            or to_int(row["balls_faced"]) < 0
            or to_int(row["wickets"]) < 0
            or to_int(row["balls_bowled"]) < 0
        )
    ]

    print(
        f"Invalid statistics values:        "
        f"{len(invalid_statistics)}"
    )

    # ========================================================================
    # RECONCILIATION
    # ========================================================================

    print()
    print("RECONCILIATION")
    print("-" * 80)

    total_team_runs = sum(
        to_int(row["runs"])
        for row in match_team
    )

    total_player_runs = sum(
        to_int(row["batting_runs"])
        for row in performances
    )

    print(
        f"Team runs:                        "
        f"{total_team_runs}"
    )

    print(
        f"Player batting runs:              "
        f"{total_player_runs}"
    )

    print(
        f"Difference:                        "
        f"{total_team_runs - total_player_runs}"
    )

    total_team_fours = sum(
        to_int(row["fours"])
        for row in match_team
    )

    total_player_fours = sum(
        to_int(row["fours"])
        for row in performances
    )

    print()
    print(
        f"Team fours:                       "
        f"{total_team_fours}"
    )

    print(
        f"Player fours:                     "
        f"{total_player_fours}"
    )

    total_team_sixes = sum(
        to_int(row["sixes"])
        for row in match_team
    )

    total_player_sixes = sum(
        to_int(row["sixes"])
        for row in performances
    )

    print()
    print(
        f"Team sixes:                       "
        f"{total_team_sixes}"
    )

    print(
        f"Player sixes:                     "
        f"{total_player_sixes}"
    )

    # ========================================================================
    # FINAL RESULT
    # ========================================================================

    failures = (
        duplicate_matches
        + duplicate_teams
        + duplicate_players
        + duplicate_match_team
        + duplicate_performances
        + duplicate_statistics
        + len(missing_player_ids)
        + len(performance_unknown_matches)
        + len(performance_unknown_teams)
        + len(invalid_batting)
        + len(invalid_bowling)
        + len(invalid_statistics)
    )

    print()
    print("=" * 80)

    if failures == 0:
        print("CSV AUDIT: PASS")
    else:
        print(
            f"CSV AUDIT: REVIEW "
            f"({failures} detected issues)"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()