import csv
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"
)

PLAYER_MATCH_FILE = BASE_DIR / "player_match_performance.csv"
PLAYER_STATS_FILE = BASE_DIR / "player_statistics.csv"


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def integer(value):
    if value in (None, ""):
        return 0

    return int(float(value))


player_matches = read_csv(PLAYER_MATCH_FILE)
player_stats = read_csv(PLAYER_STATS_FILE)


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

    e["runs"] += integer(row["batting_runs"])
    e["balls_faced"] += integer(row["balls_faced"])
    e["fours"] += integer(row["fours"])
    e["sixes"] += integer(row["sixes"])

    if row["not_out"].lower() == "true":
        e["not_outs"] += 1

    e["wickets"] += integer(row["wickets"])
    e["balls_bowled"] += integer(row["balls_bowled"])
    e["runs_conceded"] += integer(row["runs_conceded"])

    wickets = integer(row["wickets"])

    if wickets >= 5:
        e["five_wicket_hauls"] += 1

    runs = integer(row["batting_runs"])

    if runs >= 100:
        e["centuries"] += 1
    elif runs >= 50:
        e["fifties"] += 1


fields = [
    "matches",
    "batting_innings",
    "runs",
    "balls_faced",
    "fours",
    "sixes",
    "not_outs",
    "wickets",
    "balls_bowled",
    "runs_conceded",
    "five_wicket_hauls",
    "centuries",
    "fifties",
]


print("=" * 100)
print("T20I CAREER MISMATCH DIAGNOSTIC")
print("=" * 100)

mismatch_count = 0

for row in player_stats:

    key = (
        row["player_external_id"],
        row["gender"]
    )

    expected_row = expected[key]

    differences = []

    for field in fields:

        actual = integer(row[field])
        expected_value = expected_row[field]

        if actual != expected_value:

            differences.append(
                (
                    field,
                    actual,
                    expected_value
                )
            )

    if differences:

        mismatch_count += 1

        print("\n" + "-" * 100)

        print(
            f"Player: {row['player_name']}"
        )

        print(
            f"External ID: {row['player_external_id']}"
        )

        print(
            f"Gender: {row['gender']}"
        )

        for field, actual, expected_value in differences:

            print(
                f"{field:<22} "
                f"CSV={actual:<8} "
                f"RECALCULATED={expected_value:<8}"
            )


print("\n" + "=" * 100)

print(
    f"Total mismatched players: {mismatch_count}"
)

print("=" * 100)