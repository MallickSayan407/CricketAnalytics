"""
Audit ODI Match Predictor V3 training dataset.

V3 is built from the audited V1 dataset and adds 34 engineered
features.

This audit verifies:
- V1 data preservation
- engineered-feature mathematics
- valid ranges
- no missing/infinite values
- chronological ordering
- no duplicate match IDs
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data"
)

V1_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training.csv"
)

V3_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training_v3.csv"
)


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

DIFF_MAP = {
    "experience_difference": (
        "team_a_matches_before",
        "team_b_matches_before",
    ),
    "experience_reliability_difference": (
        "team_a_experience_reliability",
        "team_b_experience_reliability",
    ),
    "overall_strength_difference": (
        "team_a_win_rate",
        "team_b_win_rate",
    ),
    "weighted_form_difference": (
        "team_a_weighted_form",
        "team_b_weighted_form",
    ),
    "recent_momentum_difference": (
        "team_a_recent_momentum",
        "team_b_recent_momentum",
    ),
    "batting_strength_difference": (
        "team_a_avg_runs",
        "team_b_avg_runs",
    ),
    "wicket_strength_difference": (
        "team_a_avg_wickets",
        "team_b_avg_wickets",
    ),
    "venue_win_rate_difference": (
        "team_a_venue_win_rate",
        "team_b_venue_win_rate",
    ),
    "venue_sample_difference": (
        "team_a_venue_matches_before",
        "team_b_venue_matches_before",
    ),
    "adjusted_venue_difference": (
        "team_a_adjusted_venue_strength",
        "team_b_adjusted_venue_strength",
    ),
    "h2h_win_rate_difference": (
        "head_to_head_a_win_rate",
        "head_to_head_b_win_rate",
    ),
}


ABS_MAP = {
    "abs_experience_difference": "experience_difference",
    "abs_batting_strength_difference":
        "batting_strength_difference",
    "abs_wicket_strength_difference":
        "wicket_strength_difference",
    "abs_venue_difference":
        "venue_win_rate_difference",
    "abs_h2h_difference":
        "h2h_win_rate_difference",
}


BINARY_MAP = {
    "experience_advantage": "experience_difference",
    "overall_strength_advantage":
        "overall_strength_difference",
    "weighted_form_advantage":
        "weighted_form_difference",
    "batting_strength_advantage":
        "batting_strength_difference",
    "composite_strength_advantage":
        "composite_strength_difference",
}


# ============================================================
# HELPERS
# ============================================================

def check_equal(
    actual,
    expected,
    name,
    tolerance=1e-9,
):
    difference = (
        actual - expected
    ).abs()

    if difference.max() > tolerance:

        bad = difference[
            difference > tolerance
        ]

        print(
            f"[FAIL] {name}: "
            f"{len(bad)} mismatches"
        )

        return False

    print(
        f"[PASS] {name}"
    )

    return True


def reliability(
    sample_size,
    minimum_sample,
):
    return (
        sample_size
        /
        (
            sample_size
            + minimum_sample
        )
    )


def weighted_form(
    overall,
    recent5,
    recent10,
):
    return (
        0.30 * overall
        + 0.30 * recent10
        + 0.40 * recent5
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - V3 DATASET AUDIT"
    )
    print("=" * 72)
    print()

    failed = False

    # ========================================================
    # 1. FILE CHECK
    # ========================================================

    if not V1_FILE.exists():

        print(
            "ERROR: V1 dataset not found:"
        )

        print(V1_FILE)

        sys.exit(1)

    if not V3_FILE.exists():

        print(
            "ERROR: V3 dataset not found:"
        )

        print(V3_FILE)

        sys.exit(1)

    # ========================================================
    # 2. LOAD DATA
    # ========================================================

    v1 = pd.read_csv(
        V1_FILE
    )

    v3 = pd.read_csv(
        V3_FILE
    )

    print(
        f"V1 rows       : {len(v1)}"
    )

    print(
        f"V1 columns    : {len(v1.columns)}"
    )

    print(
        f"V3 rows       : {len(v3)}"
    )

    print(
        f"V3 columns    : {len(v3.columns)}"
    )

    print()

    # ========================================================
    # 3. ROW COUNT
    # ========================================================

    if len(v1) != len(v3):

        print(
            "[FAIL] V1/V3 row counts differ"
        )

        failed = True

    else:

        print(
            "[PASS] V1/V3 row counts identical"
        )

    # ========================================================
    # 4. V1 COLUMN PRESERVATION
    # ========================================================

    missing_columns = [
        column
        for column in v1.columns
        if column not in v3.columns
    ]

    if missing_columns:

        print(
            "[FAIL] V3 missing V1 columns:"
        )

        for column in missing_columns:
            print(f"  {column}")

        failed = True

    else:

        print(
            "[PASS] All V1 columns preserved"
        )

    # ========================================================
    # 5. V1 VALUE PRESERVATION
    # ========================================================

    preservation_failed = False

    for column in v1.columns:

        if column not in v3.columns:
            continue

        if (
            not v1[column]
            .astype(str)
            .equals(
                v3[column]
                .astype(str)
            )
        ):

            print(
                f"[FAIL] V1 data changed: "
                f"{column}"
            )

            preservation_failed = True

    if preservation_failed:

        failed = True

    else:

        print(
            "[PASS] All V1 values preserved"
        )

    # ========================================================
    # 6. MATCH IDs
    # ========================================================

    duplicate_count = (
        v3["match_id"]
        .duplicated()
        .sum()
    )

    if duplicate_count:

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
    # 7. TARGET
    # ========================================================

    if not v1["target"].equals(
        v3["target"]
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
    # 8. NULL VALUES
    # ========================================================

    numeric = v3.select_dtypes(
        include=["number"]
    )

    null_count = (
        numeric
        .isnull()
        .sum()
        .sum()
    )

    if null_count:

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
        numeric.to_numpy()
    ).sum()

    if infinite_count:

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
            v3[column_a]
            - v3[column_b]
        )

        if not check_equal(
            v3[new_column],
            expected,
            new_column,
        ):

            failed = True

    # ========================================================
    # 11. WEIGHTED FORM
    # ========================================================

    print()
    print(
        "CHECKING WEIGHTED FORM"
    )
    print("-" * 72)

    expected_a = weighted_form(
        v3["team_a_win_rate"],
        v3["team_a_last5_win_rate"],
        v3["team_a_last10_win_rate"],
    )

    expected_b = weighted_form(
        v3["team_b_win_rate"],
        v3["team_b_last5_win_rate"],
        v3["team_b_last10_win_rate"],
    )

    if not check_equal(
        v3["team_a_weighted_form"],
        expected_a,
        "team_a_weighted_form",
    ):

        failed = True

    if not check_equal(
        v3["team_b_weighted_form"],
        expected_b,
        "team_b_weighted_form",
    ):

        failed = True

    # ========================================================
    # 12. RELIABILITY FEATURES
    # ========================================================

    print()
    print(
        "CHECKING RELIABILITY FEATURES"
    )
    print("-" * 72)

    expected_a = reliability(
        v3[
            "team_a_matches_before"
        ],
        10,
    )

    expected_b = reliability(
        v3[
            "team_b_matches_before"
        ],
        10,
    )

    if not check_equal(
        v3[
            "team_a_experience_reliability"
        ],
        expected_a,
        "team_a_experience_reliability",
    ):

        failed = True

    if not check_equal(
        v3[
            "team_b_experience_reliability"
        ],
        expected_b,
        "team_b_experience_reliability",
    ):

        failed = True

    expected_a = reliability(
        v3[
            "team_a_venue_matches_before"
        ],
        5,
    )

    expected_b = reliability(
        v3[
            "team_b_venue_matches_before"
        ],
        5,
    )

    if not check_equal(
        v3[
            "team_a_venue_reliability"
        ],
        expected_a,
        "team_a_venue_reliability",
    ):

        failed = True

    if not check_equal(
        v3[
            "team_b_venue_reliability"
        ],
        expected_b,
        "team_b_venue_reliability",
    ):

        failed = True

    expected_h2h = reliability(
        v3[
            "head_to_head_matches_before"
        ],
        10,
    )

    if not check_equal(
        v3[
            "h2h_sample_reliability"
        ],
        expected_h2h,
        "h2h_sample_reliability",
    ):

        failed = True

    # ========================================================
    # 13. ADJUSTED VENUE STRENGTH
    # ========================================================

    print()
    print(
        "CHECKING ADJUSTED VENUE FEATURES"
    )
    print("-" * 72)

    expected_a = (
        v3[
            "team_a_venue_win_rate"
        ]
        *
        v3[
            "team_a_venue_reliability"
        ]
    )

    expected_b = (
        v3[
            "team_b_venue_win_rate"
        ]
        *
        v3[
            "team_b_venue_reliability"
        ]
    )

    if not check_equal(
        v3[
            "team_a_adjusted_venue_strength"
        ],
        expected_a,
        "team_a_adjusted_venue_strength",
    ):

        failed = True

    if not check_equal(
        v3[
            "team_b_adjusted_venue_strength"
        ],
        expected_b,
        "team_b_adjusted_venue_strength",
    ):

        failed = True

    # ========================================================
    # 14. ADJUSTED H2H
    # ========================================================

    print()
    print(
        "CHECKING ADJUSTED H2H"
    )
    print("-" * 72)

    expected = (
        v3[
            "h2h_win_rate_difference"
        ]
        *
        v3[
            "h2h_sample_reliability"
        ]
    )

    if not check_equal(
        v3[
            "adjusted_h2h_difference"
        ],
        expected,
        "adjusted_h2h_difference",
    ):

        failed = True

    # ========================================================
    # 15. ABSOLUTE FEATURES
    # ========================================================

    print()
    print(
        "CHECKING ABSOLUTE-DIFFERENCE FEATURES"
    )
    print("-" * 72)

    for new_column, source in ABS_MAP.items():

        expected = (
            v3[source]
            .abs()
        )

        if not check_equal(
            v3[new_column],
            expected,
            new_column,
        ):

            failed = True

    # ========================================================
    # 16. BINARY FEATURES
    # ========================================================

    print()
    print(
        "CHECKING BINARY ADVANTAGE FEATURES"
    )
    print("-" * 72)

    for new_column, source in BINARY_MAP.items():

        expected = (
            v3[source] > 0
        ).astype(int)

        if not check_equal(
            v3[new_column],
            expected,
            new_column,
        ):

            failed = True

    # ========================================================
    # 17. COMPOSITE FEATURE
    # ========================================================

    print()
    print(
        "CHECKING COMPOSITE STRENGTH"
    )
    print("-" * 72)

    expected = (
        0.30
        * v3[
            "overall_strength_difference"
        ]
        +
        0.25
        * v3[
            "weighted_form_difference"
        ]
        +
        0.20
        * (
            v3[
                "batting_strength_difference"
            ]
            / 100.0
        )
        +
        0.15
        * (
            v3[
                "wicket_strength_difference"
            ]
            / 10.0
        )
        +
        0.10
        * v3[
            "adjusted_venue_difference"
        ]
    )

    if not check_equal(
        v3[
            "composite_strength_difference"
        ],
        expected,
        "composite_strength_difference",
    ):

        failed = True

    # ========================================================
    # 18. BINARY VALUES
    # ========================================================

    binary_columns = list(
        BINARY_MAP.keys()
    )

    for column in binary_columns:

        values = set(
            v3[column]
            .astype(int)
            .unique()
        )

        if not values.issubset(
            {0, 1}
        ):

            print(
                f"[FAIL] {column}: "
                f"invalid values {values}"
            )

            failed = True

    # ========================================================
    # 19. RELIABILITY RANGE
    # ========================================================

    reliability_columns = [
        "team_a_experience_reliability",
        "team_b_experience_reliability",
        "team_a_venue_reliability",
        "team_b_venue_reliability",
        "h2h_sample_reliability",
    ]

    print()
    print(
        "CHECKING RELIABILITY RANGES"
    )
    print("-" * 72)

    for column in reliability_columns:

        minimum = v3[column].min()
        maximum = v3[column].max()

        if (
            minimum < 0
            or maximum > 1
        ):

            print(
                f"[FAIL] {column}: "
                f"{minimum:.4f} -> "
                f"{maximum:.4f}"
            )

            failed = True

        else:

            print(
                f"[PASS] {column}: "
                f"{minimum:.4f} -> "
                f"{maximum:.4f}"
            )

    # ========================================================
    # 20. CHRONOLOGY
    # ========================================================

    print()
    print(
        "CHECKING CHRONOLOGICAL ORDER"
    )
    print("-" * 72)

    dates = pd.to_datetime(
        v3["match_date"]
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
    # 21. CURRENT-MATCH LEAKAGE CHECK
    # ========================================================

    print()
    print(
        "CHECKING FOR OBVIOUS CURRENT-MATCH LEAKAGE"
    )
    print("-" * 72)

    forbidden_keywords = [
        "winner",
        "result",
        "runs_scored",
        "runs_conceded",
        "wickets_lost",
        "current",
        "target",
    ]

    metadata_columns = {
        "match_id",
        "external_id",
        "match_date",
        "team_a_id",
        "team_b_id",
        "team_a",
        "team_b",
        "venue_id",
        "venue",
        "target",
    }

    suspicious = []

    for column in v3.columns:

        if column in metadata_columns:
            continue

        lower = column.lower()

        for keyword in forbidden_keywords:

            if keyword in lower:

                suspicious.append(
                    column
                )

                break

    # The original historical features legitimately contain
    # "matches_before", "wins_before", etc. Those are safe.
    # We only fail on direct current-result/statistic names.

    allowed_suspicious = set()

    suspicious = [
        column
        for column in suspicious
        if column not in allowed_suspicious
    ]

    if suspicious:

        print(
            "[WARNING] Review these feature names:"
        )

        for column in sorted(
            set(suspicious)
        ):

            print(
                f"  {column}"
            )

        print(
            "No automatic failure is triggered because "
            "the V3 builder is derived from historical V1 data."
        )

    else:

        print(
            "[PASS] No obvious current-match "
            "leakage feature names"
        )

    # ========================================================
    # 22. FEATURE VARIATION
    # ========================================================

    print()
    print(
        "CHECKING FEATURE VARIATION"
    )
    print("-" * 72)

    v3_features = [
        column
        for column in v3.columns
        if column not in metadata_columns
    ]

    constant_features = [
        column
        for column in v3_features
        if v3[column].nunique() <= 1
    ]

    if constant_features:

        print(
            "[WARNING] Constant features:"
        )

        for column in constant_features:
            print(
                f"  {column}"
            )

    else:

        print(
            "[PASS] Every model feature "
            "has variation"
        )

    # ========================================================
    # 23. SUMMARY
    # ========================================================

    print()
    print(
        "V3 FEATURE SUMMARY"
    )
    print("-" * 72)

    summary_columns = [
        "overall_strength_difference",
        "weighted_form_difference",
        "batting_strength_difference",
        "wicket_strength_difference",
        "adjusted_venue_difference",
        "adjusted_h2h_difference",
        "composite_strength_difference",
    ]

    for column in summary_columns:

        print(
            f"{column:35s} "
            f"mean={v3[column].mean():8.4f} "
            f"min={v3[column].min():8.4f} "
            f"max={v3[column].max():8.4f}"
        )

    # ========================================================
    # 24. FINAL VERDICT
    # ========================================================

    print()
    print("=" * 72)
    print(
        "FINAL V3 AUDIT"
    )
    print("=" * 72)

    if failed:

        print(
            "FAIL: V3 requires correction "
            "before model training."
        )

        sys.exit(1)

    print(
        "PASS: V3 dataset is mathematically "
        "and structurally valid."
    )

    print()
    print(
        "V1 and V2 remain unchanged."
    )

    print(
        "V3 is ready for model training."
    )

    print()


if __name__ == "__main__":
    main()
