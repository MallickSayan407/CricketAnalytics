import csv
import zipfile
from collections import defaultdict

from process_ipl_dataset import (
    process_player_match_performance,
    normalize_team,
)


ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\ipl\ipl_json.zip"


def load_match(match_id):
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        filename = f"{match_id}.json"

        if filename not in z.namelist():
            raise FileNotFoundError(
                f"{filename} not found inside {ZIP_PATH}"
            )

        with z.open(filename) as f:
            import json
            return json.load(f)


def main():
    print("=" * 80)
    print("IPL ALL-ROUNDER ACCUMULATION TEST")
    print("=" * 80)

    # A known IPL match containing players who both bat and bowl.
    match_id = "1082591"

    data = load_match(match_id)
    info = data["info"]

    print(f"Match ID: {match_id}")
    print(f"Teams: {info['teams']}")

    rows = process_player_match_performance(
        match_id,
        info,
        data["innings"],
    )

    print(f"Player-match rows: {len(rows)}")

    all_rounders = []

    for row in rows:
        if (
            row.get("batting_runs", 0) > 0
            and row.get("balls_bowled", 0) > 0
        ):
            all_rounders.append(row)

    print()
    print("Players with both batting and bowling activity:")
    print("-" * 80)

    for row in all_rounders:
        print(
            f"{row['player_name']}: "
            f"runs={row['batting_runs']}, "
            f"balls_faced={row['balls_faced']}, "
            f"fours={row['fours']}, "
            f"sixes={row['sixes']}, "
            f"balls_bowled={row['balls_bowled']}, "
            f"runs_conceded={row['runs_conceded']}, "
            f"wickets={row['wickets']}"
        )

    if not all_rounders:
        raise AssertionError(
            "No player was detected with both batting and bowling activity. "
            "Choose another match containing an all-rounder."
        )

    # Basic correctness checks.
    for row in all_rounders:
        assert row["batting_runs"] > 0
        assert row["balls_faced"] > 0
        assert row["balls_bowled"] > 0

    print()
    print("=" * 80)
    print("ALL-ROUNDER ACCUMULATION TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()