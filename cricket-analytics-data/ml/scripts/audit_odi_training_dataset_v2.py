"""
Audit ODI Match Predictor V2 training dataset.

V2 contains the original V1 features plus engineered relative features.

Checks:
1. File existence
2. Row/column counts
3. Match identity preservation
4. Target preservation
5. Duplicate match IDs
6. NULL values
7. Infinite values
8. Difference feature mathematics
9. Ratio feature mathematics
10. Absolute-difference mathematics
11. Advantage feature mathematics
12. Valid feature ranges
13. Chronological ordering
14. Feature variation
15. Final verdict
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"D:\CricketAnalytics\cricket-analytics-data")

V1_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training.csv"
)

V2_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training_v2.csv"
)


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

DIFF_MAP = {
    "matches_before_difference": (
        "team_a_matches_before",
        "team_b_matches_before",
    ),
    "wins_before_difference": (
        "team_a_wins_before",
        "team_b_wins_before",
    ),
    "decided_matches_difference": (
        "team_a_decided_matches_before",
        "team_b_decided_matches_before",
    ),
    "win_rate_difference": (
        "team_a_win_rate",
        "team_b_win_rate",
    ),
    "last5_win_rate_difference": (
        "team_a_last5_win_rate",
        "team_b_last5_win_rate",
    ),
    "last10_win_rate_difference": (
        "team_a_last10_win_rate",
        "team_b_last10_win_rate",
    ),
    "avg_runs_difference": (
        "team_a_avg_runs",
        "team_b_avg_runs",
    ),
    "avg_wickets_difference": (
        "team_a_avg_wickets",
        "team_b_avg_wickets",
    ),
    "venue_matches_difference": (
        "team_a_venue_matches_before",
        "team_b_venue_matches_before",
    ),
    "venue_win_rate_difference": (
        "team_a_venue_win_rate",
        "team_b_venue_win_rate",
    ),
    "h2h_wins_difference": (
        "head_to_head_a_wins",
        "head_to_head_b_wins",
    ),
    "h2h_win_rate_difference": (
        "head_to_head_a_win_rate",
        "head_to_head_b_win_rate",
    ),
}


RATIO_MAP = {
    "experience_ratio": (
        "team_a_matches_before",
        "team_b_matches_before",
    ),
    "win_count_ratio": (
        "team_a_wins_before",
        "team_b_wins_before",
    ),
    "avg_runs_ratio": (
        "team_a_avg_runs",
        "team_b_avg_runs",
    ),
    "avg_wickets_ratio": (
        "team_a_avg_wickets",
        "team_b_avg_wickets",
    ),
}


ABS_MAP = {
    "abs_win_rate_difference": "win_rate_difference",
    "abs_last5_difference": "last5_win_rate_difference",
    "abs_last10_difference": "last10_win_rate_difference",
    "abs_avg_runs_difference": "avg_runs_difference",
    "abs_avg_wickets_difference": "avg_wickets_difference",
}


ADVANTAGE_MAP = {
    "team_a_win_rate_advantage": "win_rate_difference",
    "team_a_recent5_advantage": "last5_win_rate_difference",
    "team_a_recent10_advantage": "last10_win_rate_difference",
    "team_a_venue_advantage": "venue_win_rate_difference",
    "team_a_h2h_advantage": "h2h_win_rate_difference",
}


# ============================================================
# HELPERS
# ============================================================

def check_equal(actual, expected, name, tolerance=1e-9):
    """
    Compare two pandas Series numerically.
    """

    difference = (actual - expected).abs()

    if difference.max() > tolerance:

        bad = difference[difference > tolerance]

        print(
            f"[FAIL] {name}: "
            f"{len(bad)} mismatches"
        )

        return False

    print(f"[PASS] {name}")

    return True


def safe_ratio_series(a, b):
    """
    Calculate A/B while safely handling zero denominators.

    The V2 builder uses 1.0 when the denominator is zero,
    so the audit reproduces that behavior.
    """

    result = np.where(
        b == 0,
        1.0,
        a / b,
    )

    return pd.Series(
        result,
        index=a.index,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("ODI MATCH PREDICTOR - V2 DATASET AUDIT")
    print("=" * 72)
    print()

    failed = False

    # ========================================================
    # 1. FILE CHECK
    # ========================================================

    if not V1_FILE.exists():

        print("ERROR: V1 dataset not found:")
        print(V1_FILE)

        sys.exit(1)

    if not V2_FILE.exists():

        print("ERROR: V2 dataset not found:")
        print(V2_FILE)

        sys.exit(1)

    # ========================================================
    # 2. LOAD DATA
    # ========================================================

    v1 = pd.read_csv(V1_FILE)
    v2 = pd.read_csv(V2_FILE)

    print(f"V1 rows       : {len(v1)}")
    print(f"V1 columns    : {len(v1.columns)}")
    print(f"V2 rows       : {len(v2)}")
    print(f"V2 columns    : {len(v2.columns)}")
    print()

    # ========================================================
    # 3. ROW COUNT
    # ========================================================

    if len(v1) != len(v2):

        print(
            "[FAIL] V1/V2 row counts differ"
        )

        failed = True

    else:

        print(
            "[PASS] V1/V2 row counts identical"
        )

    # ========================================================
    # 4. REQUIRED V1 COLUMNS
    # ========================================================

    missing_v1_columns = [
        column
        for column in v1.columns
        if column not in v2.columns
    ]

    if missing_v1_columns:

        print(
            "[FAIL] V2 is missing V1 columns:"
        )

        for column in missing_v1_columns:
            print(f"  {column}")

        failed = True

    else:

        print(
            "[PASS] All V1 columns preserved"
        )

    # ========================================================
    # 5. MATCH IDENTITY
    # ========================================================

    identity_columns = [
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

    for column in identity_columns:

        if column not in v2.columns:

            print(
                f"[FAIL] Missing identity column: "
                f"{column}"
            )

            failed = True

            continue

        if not v1[column].astype(str).equals(
            v2[column].astype(str)
        ):

            print(
                f"[FAIL] Identity changed: "
                f"{column}"
            )

            failed = True

    if not failed:

        print(
            "[PASS] Match identity columns unchanged"
        )

    # ========================================================
    # 6. TARGET
    # ========================================================

    if not v1["target"].equals(
        v2["target"]
    ):

        print(
            "[FAIL] Target changed"
        )

        failed = True

    else:

        print(
            "[PASS] Target unchanged"
        )

    # ========================================================
    # 7. DUPLICATE MATCH IDS
    # ========================================================

    duplicate_count = (
        v2["match_id"]
        .duplicated()
        .sum()
    )

    if duplicate_count > 0:

        print(
            f"[FAIL] Duplicate match IDs: "
            f"{duplicate_count}"
        )

        failed = True

    else:

        print(
            "[PASS] Duplicate match IDs = 0"
        )

    # ========================================================
    # 8. NULL VALUES
    # ========================================================

    numeric_columns = (
        v2.select_dtypes(
            include=["number"]
        )
    )

    null_count = (
        numeric_columns
        .isnull()
        .sum()
        .sum()
    )

    if null_count > 0:

        print(
            f"[FAIL] Numeric NULL values: "
            f"{null_count}"
        )

        failed = True

    else:

        print(
            "[PASS] Numeric NULL values = 0"
        )

    # ========================================================
    # 9. INFINITE VALUES
    # ========================================================

    infinite_count = np.isinf(
        numeric_columns.to_numpy()
    ).sum()

    if infinite_count > 0:

        print(
            f"[FAIL] Infinite numeric values: "
            f"{infinite_count}"
        )

        failed = True

    else:

        print(
            "[PASS] Infinite numeric values = 0"
        )

    # ========================================================
    # 10. DIFFERENCE FEATURES
    # ========================================================

    print()
    print(
        "CHECKING DIFFERENCE FEATURES"
    )
    print("-" * 72)

    for new_column, (
        column_a,
        column_b,
    ) in DIFF_MAP.items():

        expected = (
            v2[column_a]
            - v2[column_b]
        )

        result = check_equal(
            v2[new_column],
            expected,
            new_column,
        )

        if not result:
            failed = True

    # ========================================================
    # 11. RATIO FEATURES
    # ========================================================

    print()
    print(
        "CHECKING RATIO FEATURES"
    )
    print("-" * 72)

    for new_column, (
        column_a,
        column_b,
    ) in RATIO_MAP.items():

        expected = safe_ratio_series(
            v2[column_a],
            v2[column_b],
        )

        result = check_equal(
            v2[new_column],
            expected,
            new_column,
        )

        if not result:
            failed = True

    # ========================================================
    # 12. ABSOLUTE DIFFERENCE FEATURES
    # ========================================================

    print()
    print(
        "CHECKING ABSOLUTE-DIFFERENCE FEATURES"
    )
    print("-" * 72)

    for new_column, source_column in ABS_MAP.items():

        expected = (
            v2[source_column]
            .abs()
        )

        result = check_equal(
            v2[new_column],
            expected,
            new_column,
        )

        if not result:
            failed = True

    # ========================================================
    # 13. ADVANTAGE FEATURES
    # ========================================================

    print()
    print(
        "CHECKING ADVANTAGE FEATURES"
    )
    print("-" * 72)

    for new_column, source_column in ADVANTAGE_MAP.items():

        expected = (
            v2[source_column] > 0
        ).astype(int)

        result = check_equal(
            v2[new_column],
            expected,
            new_column,
        )

        if not result:
            failed = True

    # ========================================================
    # 14. ACTUAL RATE RANGES
    # ========================================================

    print()
    print(
        "CHECKING ACTUAL RATE RANGES"
    )
    print("-" * 72)

    rate_columns = [
        "team_a_win_rate",
        "team_a_last5_win_rate",
        "team_a_last10_win_rate",
        "team_b_win_rate",
        "team_b_last5_win_rate",
        "team_b_last10_win_rate",
        "team_a_venue_win_rate",
        "team_b_venue_win_rate",
        "head_to_head_a_win_rate",
        "head_to_head_b_win_rate",
    ]

    for column in rate_columns:

        minimum = v2[column].min()
        maximum = v2[column].max()

        if (
            minimum < 0
            or maximum > 1
        ):

            print(
                f"[FAIL] {column}: "
                f"outside [0,1]"
            )

            failed = True

        else:

            print(
                f"[PASS] {column}: "
                f"{minimum:.4f} -> "
                f"{maximum:.4f}"
            )

    # ========================================================
    # 15. RATE DIFFERENCE RANGES
    # ========================================================

    print()
    print(
        "CHECKING RATE-DIFFERENCE RANGES"
    )
    print("-" * 72)

    rate_difference_columns = [
        "win_rate_difference",
        "last5_win_rate_difference",
        "last10_win_rate_difference",
        "venue_win_rate_difference",
        "h2h_win_rate_difference",
    ]

    for column in rate_difference_columns:

        minimum = v2[column].min()
        maximum = v2[column].max()

        if (
            minimum < -1
            or maximum > 1
        ):

            print(
                f"[FAIL] {column}: "
                f"outside [-1,1]"
            )

            failed = True

        else:

            print(
                f"[PASS] {column}: "
                f"{minimum:.4f} -> "
                f"{maximum:.4f}"
            )

    # ========================================================
    # 16. ABSOLUTE RATE DIFFERENCE RANGES
    # ========================================================

    print()
    print(
        "CHECKING ABSOLUTE-DIFFERENCE RANGES"
    )
    print("-" * 72)

    absolute_rate_columns = [
        "abs_win_rate_difference",
        "abs_last5_difference",
        "abs_last10_difference",
    ]

    for column in absolute_rate_columns:

        minimum = v2[column].min()
        maximum = v2[column].max()

        if (
            minimum < 0
            or maximum > 1
        ):

            print(
                f"[FAIL] {column}: "
                f"outside [0,1]"
            )

            failed = True

        else:

            print(
                f"[PASS] {column}: "
                f"{minimum:.4f} -> "
                f"{maximum:.4f}"
            )

    # ========================================================
    # 17. ADVANTAGE RANGE
    # ========================================================

    print()
    print(
        "CHECKING ADVANTAGE RANGES"
    )
    print("-" * 72)

    advantage_columns = [
        "team_a_win_rate_advantage",
        "team_a_recent5_advantage",
        "team_a_recent10_advantage",
        "team_a_venue_advantage",
        "team_a_h2h_advantage",
    ]

    for column in advantage_columns:

        values = set(
            v2[column]
            .astype(int)
            .unique()
        )

        if not values.issubset({0, 1}):

            print(
                f"[FAIL] {column}: "
                f"invalid values {values}"
            )

            failed = True

        else:

            print(
                f"[PASS] {column}: "
                f"binary {sorted(values)}"
            )

    # ========================================================
    # 18. RATIO VALIDITY
    # ========================================================

    print()
    print(
        "CHECKING RATIO FEATURES"
    )
    print("-" * 72)

    ratio_columns = list(
        RATIO_MAP.keys()
    )

    for column in ratio_columns:

        minimum = v2[column].min()
        maximum = v2[column].max()

        if (
            not np.isfinite(minimum)
            or not np.isfinite(maximum)
        ):

            print(
                f"[FAIL] {column}: "
                "non-finite range"
            )

            failed = True

        elif minimum < 0:

            print(
                f"[FAIL] {column}: "
                f"negative ratio"
            )

            failed = True

        else:

            print(
                f"[PASS] {column}: "
                f"{minimum:.4f} -> "
                f"{maximum:.4f}"
            )

    # ========================================================
    # 19. CHRONOLOGICAL ORDER
    # ========================================================

    print()
    print(
        "CHECKING CHRONOLOGICAL ORDER"
    )
    print("-" * 72)

    dates = pd.to_datetime(
        v2["match_date"]
    )

    if dates.is_monotonic_increasing:

        print(
            "[PASS] Chronological order preserved"
        )

    else:

        print(
            "[FAIL] Dataset is not chronological"
        )

        failed = True

    # ========================================================
    # 20. FEATURE VARIATION
    # ========================================================

    print()
    print(
        "CHECKING FEATURE VARIATION"
    )
    print("-" * 72)

    new_columns = (
        list(DIFF_MAP.keys())
        + list(RATIO_MAP.keys())
        + list(ABS_MAP.keys())
        + list(ADVANTAGE_MAP.keys())
    )

    constant_features = []

    for column in new_columns:

        unique_count = (
            v2[column]
            .nunique()
        )

        if unique_count <= 1:

            constant_features.append(
                column
            )

    if constant_features:

        print(
            "[WARNING] Constant V2 features:"
        )

        for column in constant_features:

            print(
                f"  {column}"
            )

    else:

        print(
            "[PASS] Every engineered feature "
            "has variation"
        )

    # ========================================================
    # 21. RELATIVE FEATURE SUMMARY
    # ========================================================

    print()
    print(
        "V2 RELATIVE FEATURE SUMMARY"
    )
    print("-" * 72)

    summary_columns = [
        "win_rate_difference",
        "last5_win_rate_difference",
        "last10_win_rate_difference",
        "avg_runs_difference",
        "avg_wickets_difference",
        "venue_win_rate_difference",
        "h2h_win_rate_difference",
    ]

    for column in summary_columns:

        print(
            f"{column:32s} "
            f"mean={v2[column].mean():8.4f} "
            f"min={v2[column].min():8.4f} "
            f"max={v2[column].max():8.4f}"
        )

    # ========================================================
    # 22. FINAL VERDICT
    # ========================================================

    print()
    print("=" * 72)
    print("FINAL V2 AUDIT")
    print("=" * 72)

    if failed:

        print(
            "FAIL: V2 requires correction "
            "before model training."
        )

        sys.exit(1)

    print(
        "PASS: V2 dataset is mathematically "
        "and structurally valid."
    )

    print()
    print(
        "V1 remains available as the baseline."
    )

    print(
        "V2 is ready for chronological "
        "model comparison."
    )

    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()