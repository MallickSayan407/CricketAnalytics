import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas is not installed.")
    print("Run: python -m pip install pandas")
    sys.exit(1)


BASE_DIR = Path(r"D:\CricketAnalytics\cricket-analytics-data")

INPUT_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training_v2.csv"
)


# ============================================================
# V1 FEATURES REQUIRED FOR V2
# ============================================================

REQUIRED_COLUMNS = [
    "team_a_matches_before",
    "team_a_wins_before",
    "team_a_decided_matches_before",
    "team_a_win_rate",
    "team_a_last5_win_rate",
    "team_a_last10_win_rate",
    "team_a_avg_runs",
    "team_a_avg_wickets",

    "team_b_matches_before",
    "team_b_wins_before",
    "team_b_decided_matches_before",
    "team_b_win_rate",
    "team_b_last5_win_rate",
    "team_b_last10_win_rate",
    "team_b_avg_runs",
    "team_b_avg_wickets",

    "team_a_venue_matches_before",
    "team_a_venue_win_rate",
    "team_b_venue_matches_before",
    "team_b_venue_win_rate",

    "head_to_head_matches_before",
    "head_to_head_a_wins",
    "head_to_head_b_wins",
    "head_to_head_a_win_rate",
    "head_to_head_b_win_rate",

    "target",
]


def safe_ratio(a, b):
    """
    Returns a neutral ratio of 1.0 when the denominator is zero.
    """
    if b == 0:
        return 1.0

    return a / b


def main():

    print("=" * 72)
    print("ODI MATCH PREDICTOR - FEATURE ENGINEERING V2")
    print("=" * 72)
    print()

    # --------------------------------------------------------
    # Load V1
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        print("ERROR: V1 dataset not found:")
        print(INPUT_FILE)
        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)

    original_rows = len(df)
    original_columns = len(df.columns)

    print(f"Input rows       : {original_rows}")
    print(f"Input columns    : {original_columns}")

    # --------------------------------------------------------
    # Validate required columns
    # --------------------------------------------------------

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        print()
        print("ERROR: Required columns missing:")

        for column in missing:
            print(f"  - {column}")

        sys.exit(1)

    print("[PASS] Required V1 columns present")

    # --------------------------------------------------------
    # Preserve chronological order
    # --------------------------------------------------------

    df["match_date"] = pd.to_datetime(
        df["match_date"]
    )

    df = df.sort_values(
        ["match_date", "match_id"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Difference features
    # --------------------------------------------------------

    print()
    print("Adding difference features...")

    df["matches_before_difference"] = (
        df["team_a_matches_before"]
        - df["team_b_matches_before"]
    )

    df["wins_before_difference"] = (
        df["team_a_wins_before"]
        - df["team_b_wins_before"]
    )

    df["decided_matches_difference"] = (
        df["team_a_decided_matches_before"]
        - df["team_b_decided_matches_before"]
    )

    df["win_rate_difference"] = (
        df["team_a_win_rate"]
        - df["team_b_win_rate"]
    )

    df["last5_win_rate_difference"] = (
        df["team_a_last5_win_rate"]
        - df["team_b_last5_win_rate"]
    )

    df["last10_win_rate_difference"] = (
        df["team_a_last10_win_rate"]
        - df["team_b_last10_win_rate"]
    )

    df["avg_runs_difference"] = (
        df["team_a_avg_runs"]
        - df["team_b_avg_runs"]
    )

    df["avg_wickets_difference"] = (
        df["team_a_avg_wickets"]
        - df["team_b_avg_wickets"]
    )

    df["venue_matches_difference"] = (
        df["team_a_venue_matches_before"]
        - df["team_b_venue_matches_before"]
    )

    df["venue_win_rate_difference"] = (
        df["team_a_venue_win_rate"]
        - df["team_b_venue_win_rate"]
    )

    df["h2h_wins_difference"] = (
        df["head_to_head_a_wins"]
        - df["head_to_head_b_wins"]
    )

    df["h2h_win_rate_difference"] = (
        df["head_to_head_a_win_rate"]
        - df["head_to_head_b_win_rate"]
    )

    # --------------------------------------------------------
    # Ratio features
    # --------------------------------------------------------

    print("Adding ratio features...")

    df["experience_ratio"] = df.apply(
        lambda row: safe_ratio(
            row["team_a_matches_before"],
            row["team_b_matches_before"],
        ),
        axis=1,
    )

    df["win_count_ratio"] = df.apply(
        lambda row: safe_ratio(
            row["team_a_wins_before"],
            row["team_b_wins_before"],
        ),
        axis=1,
    )

    df["avg_runs_ratio"] = df.apply(
        lambda row: safe_ratio(
            row["team_a_avg_runs"],
            row["team_b_avg_runs"],
        ),
        axis=1,
    )

    df["avg_wickets_ratio"] = df.apply(
        lambda row: safe_ratio(
            row["team_a_avg_wickets"],
            row["team_b_avg_wickets"],
        ),
        axis=1,
    )

    # --------------------------------------------------------
    # Absolute differences
    # --------------------------------------------------------

    print("Adding magnitude features...")

    df["abs_win_rate_difference"] = (
        df["win_rate_difference"].abs()
    )

    df["abs_last5_difference"] = (
        df["last5_win_rate_difference"].abs()
    )

    df["abs_last10_difference"] = (
        df["last10_win_rate_difference"].abs()
    )

    df["abs_avg_runs_difference"] = (
        df["avg_runs_difference"].abs()
    )

    df["abs_avg_wickets_difference"] = (
        df["avg_wickets_difference"].abs()
    )

    # --------------------------------------------------------
    # Advantage indicators
    # --------------------------------------------------------

    print("Adding advantage indicators...")

    df["team_a_win_rate_advantage"] = (
        df["win_rate_difference"] > 0
    ).astype(int)

    df["team_a_recent5_advantage"] = (
        df["last5_win_rate_difference"] > 0
    ).astype(int)

    df["team_a_recent10_advantage"] = (
        df["last10_win_rate_difference"] > 0
    ).astype(int)

    df["team_a_venue_advantage"] = (
        df["venue_win_rate_difference"] > 0
    ).astype(int)

    df["team_a_h2h_advantage"] = (
        df["h2h_win_rate_difference"] > 0
    ).astype(int)

    # --------------------------------------------------------
    # Restore date format for CSV
    # --------------------------------------------------------

    df["match_date"] = df["match_date"].dt.strftime(
        "%Y-%m-%d"
    )

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    print()
    print("VALIDATING V2")
    print("-" * 72)

    if len(df) != original_rows:
        raise RuntimeError(
            "Row count changed."
        )

    if df["match_id"].duplicated().any():
        raise RuntimeError(
            "Duplicate match IDs detected."
        )

    if df.isnull().any().any():
        null_columns = df.columns[
            df.isnull().any()
        ].tolist()

        raise RuntimeError(
            "NULL values detected: "
            + ", ".join(null_columns)
        )

    target_values = set(
        df["target"].astype(int)
    )

    if target_values != {0, 1}:
        raise RuntimeError(
            f"Invalid target values: {target_values}"
        )

    print("[PASS] Row count unchanged")
    print("[PASS] Match IDs unique")
    print("[PASS] No NULL values")
    print("[PASS] Target remains binary")
    print("[PASS] V1 data preserved")

    # --------------------------------------------------------
    # Save V2
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    new_columns = [
        column
        for column in df.columns
        if column not in REQUIRED_COLUMNS
        and column not in [
            "match_id",
            "external_id",
            "match_date",
            "team_a_id",
            "team_a",
            "team_b_id",
            "team_b",
            "venue_id",
            "venue",
        ]
    ]

    print()
    print("DATASET SUMMARY")
    print("-" * 72)
    print(f"V1 columns        : {original_columns}")
    print(f"V2 columns        : {len(df.columns)}")
    print(f"New columns       : {len(df.columns) - original_columns}")
    print(f"Rows              : {len(df)}")

    print()
    print("NEW FEATURES")
    print("-" * 72)

    for column in new_columns:
        print(f"  {column}")

    print()
    print("OUTPUT")
    print("-" * 72)
    print(OUTPUT_FILE)

    print()
    print("=" * 72)
    print("V2 FEATURE ENGINEERING COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()