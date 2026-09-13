import csv
from pathlib import Path


BASE_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"
)

PLAYER_MATCH_FILE = BASE_DIR / "player_match_performance.csv"
PLAYER_STATS_FILE = BASE_DIR / "player_statistics.csv"


TARGETS = {
    "afbc53ba",
    "04ab1575",
    "f8279d15",
}


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

    return int(float(value))


player_matches = read_csv(PLAYER_MATCH_FILE)
player_stats = read_csv(PLAYER_STATS_FILE)


print("=" * 110)
print("T20I BOWLING MISMATCH INSPECTION")
print("=" * 110)


for external_id in TARGETS:

    rows = [
        row
        for row in player_matches
        if row["player_external_id"] == external_id
    ]

    career_rows = [
        row
        for row in player_stats
        if row["player_external_id"] == external_id
    ]

    print("\n")
    print("=" * 110)

    if not rows:
        print(f"No player-match rows found for {external_id}")
        continue

    player_name = rows[0]["player_name"]
    gender = rows[0]["gender"]

    print(f"PLAYER       : {player_name}")
    print(f"EXTERNAL ID  : {external_id}")
    print(f"GENDER       : {gender}")
    print("=" * 110)

    print(
        f"{'Match ID':<12}"
        f"{'Team':<30}"
        f"{'Balls':>8}"
        f"{'Runs Conc.':>12}"
        f"{'Wickets':>10}"
        f"{'Economy':>10}"
    )

    print("-" * 110)

    total_runs = 0
    total_balls = 0
    total_wickets = 0

    for row in rows:

        balls = integer(row["balls_bowled"])
        runs = integer(row["runs_conceded"])
        wickets = integer(row["wickets"])

        total_runs += runs
        total_balls += balls
        total_wickets += wickets

        economy = float(
            row["bowling_economy"] or 0
        )

        print(
            f"{row['match_id']:<12}"
            f"{row['team_name']:<30}"
            f"{balls:>8}"
            f"{runs:>12}"
            f"{wickets:>10}"
            f"{economy:>10.2f}"
        )

    print("-" * 110)

    print(
        f"{'CALCULATED TOTAL':<42}"
        f"{total_balls:>8}"
        f"{total_runs:>12}"
        f"{total_wickets:>10}"
    )

    if career_rows:

        career = career_rows[0]

        print("\nCareer CSV:")

        print(
            f"runs_conceded = "
            f"{career['runs_conceded']}"
        )

        print(
            f"balls_bowled  = "
            f"{career['balls_bowled']}"
        )

        print(
            f"wickets       = "
            f"{career['wickets']}"
        )

    print("\nPlayer-match bowling rows:")

    for row in rows:

        balls = integer(row["balls_bowled"])
        runs = integer(row["runs_conceded"])
        wickets = integer(row["wickets"])

        if balls > 0 or runs > 0:

            print(
                f"  Match {row['match_id']} | "
                f"team={row['team_name']} | "
                f"runs={runs} | "
                f"balls={balls} | "
                f"wickets={wickets}"
            )


print("\n")
print("=" * 110)
print("END")
print("=" * 110)