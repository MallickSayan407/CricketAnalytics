"""
ODI Match Predictor - V3 Training Dataset Builder

V3 is built from the already audited V1 dataset.

Design goals:
- Keep the same 2,440 eligible ODI matches.
- Preserve chronological order.
- Preserve every V1 column.
- Add robust relative-strength features.
- Avoid raw team IDs/names as model features.
- Avoid unstable ratio features as primary signals.
- Never use current-match outcome/statistics as features.

Input:
    ml/datasets/odi_match_training.csv

Output:
    ml/datasets/odi_match_training_v3.csv
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data"
)

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
    / "odi_match_training_v3.csv"
)


# ============================================================
# HELPERS
# ============================================================

def safe_rate(
    numerator,
    denominator,
):
    """
    Safe division for historical rates.

    If there is no historical sample, use 0.0.
    """

    return np.where(
        denominator > 0,
        numerator / denominator,
        0.0,
    )


def weighted_form(
    overall_rate,
    recent5_rate,
    recent10_rate,
):
    """
    Give recent form more importance while retaining
    long-term strength.

    Weights:
        overall = 0.30
        last 10 = 0.30
        last 5  = 0.40
    """

    return (
        0.30 * overall_rate
        + 0.30 * recent10_rate
        + 0.40 * recent5_rate
    )


def reliability(
    sample_size,
    minimum_sample=10,
):
    """
    Convert sample size into a bounded reliability score.

    0 samples -> 0
    10 samples -> 0.5
    20 samples -> ~0.667
    large sample -> approaches 1

    This prevents tiny historical samples from being treated
    as equally reliable as large samples.
    """

    return (
        sample_size
        / (
            sample_size
            + minimum_sample
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - V3 DATASET BUILDER"
    )
    print("=" * 72)
    print()

    # ========================================================
    # 1. FILE CHECK
    # ========================================================

    if not INPUT_FILE.exists():

        print(
            "ERROR: V1 dataset not found:"
        )

        print(INPUT_FILE)

        sys.exit(1)

    # ========================================================
    # 2. LOAD V1
    # ========================================================

    df = pd.read_csv(
        INPUT_FILE
    )

    print(
        f"Input rows    : {len(df)}"
    )

    print(
        f"Input columns : {len(df.columns)}"
    )

    print()

    # ========================================================
    # 3. REQUIRED COLUMNS
    # ========================================================

    required_columns = [
        "match_id",
        "match_date",
        "target",

        "team_a_matches_before",
        "team_b_matches_before",

        "team_a_wins_before",
        "team_b_wins_before",

        "team_a_decided_matches_before",
        "team_b_decided_matches_before",

        "team_a_win_rate",
        "team_b_win_rate",

        "team_a_last5_win_rate",
        "team_b_last5_win_rate",

        "team_a_last10_win_rate",
        "team_b_last10_win_rate",

        "team_a_avg_runs",
        "team_b_avg_runs",

        "team_a_avg_wickets",
        "team_b_avg_wickets",

        "team_a_venue_matches_before",
        "team_b_venue_matches_before",

        "team_a_venue_win_rate",
        "team_b_venue_win_rate",

        "head_to_head_matches_before",

        "head_to_head_a_wins",
        "head_to_head_b_wins",

        "head_to_head_a_win_rate",
        "head_to_head_b_win_rate",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        print(
            "ERROR: Missing required columns:"
        )

        for column in missing:
            print(f"  {column}")

        sys.exit(1)

    print(
        "[PASS] Required V1 columns present"
    )

    # ========================================================
    # 4. PRESERVE ORIGINAL ORDER
    # ========================================================

    df["match_date"] = pd.to_datetime(
        df["match_date"]
    )

    df = df.sort_values(
        [
            "match_date",
            "match_id",
        ]
    ).reset_index(
        drop=True
    )

    # ========================================================
    # 5. BASIC VALIDATION
    # ========================================================

    if df["match_id"].duplicated().any():

        print(
            "ERROR: Duplicate match IDs."
        )

        sys.exit(1)

    if df.isnull().any().any():

        print(
            "ERROR: Input contains NULL values."
        )

        sys.exit(1)

    # ========================================================
    # 6. ROBUST EXPERIENCE FEATURES
    # ========================================================

    df[
        "experience_difference"
    ] = (
        df["team_a_matches_before"]
        - df["team_b_matches_before"]
    )

    df[
        "experience_advantage"
    ] = (
        df[
            "experience_difference"
        ] > 0
    ).astype(int)

    df[
        "team_a_experience_reliability"
    ] = reliability(
        df[
            "team_a_matches_before"
        ]
    )

    df[
        "team_b_experience_reliability"
    ] = reliability(
        df[
            "team_b_matches_before"
        ]
    )

    df[
        "experience_reliability_difference"
    ] = (
        df[
            "team_a_experience_reliability"
        ]
        -
        df[
            "team_b_experience_reliability"
        ]
    )

    # ========================================================
    # 7. OVERALL STRENGTH FEATURES
    # ========================================================

    df[
        "overall_strength_difference"
    ] = (
        df["team_a_win_rate"]
        -
        df["team_b_win_rate"]
    )

    df[
        "overall_strength_advantage"
    ] = (
        df[
            "overall_strength_difference"
        ] > 0
    ).astype(int)

    # ========================================================
    # 8. RECENT FORM FEATURES
    # ========================================================

    df[
        "team_a_weighted_form"
    ] = weighted_form(
        df["team_a_win_rate"],
        df["team_a_last5_win_rate"],
        df["team_a_last10_win_rate"],
    )

    df[
        "team_b_weighted_form"
    ] = weighted_form(
        df["team_b_win_rate"],
        df["team_b_last5_win_rate"],
        df["team_b_last10_win_rate"],
    )

    df[
        "weighted_form_difference"
    ] = (
        df[
            "team_a_weighted_form"
        ]
        -
        df[
            "team_b_weighted_form"
        ]
    )

    df[
        "weighted_form_advantage"
    ] = (
        df[
            "weighted_form_difference"
        ] > 0
    ).astype(int)

    # How much recent form differs from long-term strength.
    df[
        "team_a_recent_momentum"
    ] = (
        df[
            "team_a_weighted_form"
        ]
        -
        df[
            "team_a_win_rate"
        ]
    )

    df[
        "team_b_recent_momentum"
    ] = (
        df[
            "team_b_weighted_form"
        ]
        -
        df[
            "team_b_win_rate"
        ]
    )

    df[
        "recent_momentum_difference"
    ] = (
        df[
            "team_a_recent_momentum"
        ]
        -
        df[
            "team_b_recent_momentum"
        ]
    )

    # ========================================================
    # 9. BATTING STRENGTH
    # ========================================================

    df[
        "batting_strength_difference"
    ] = (
        df["team_a_avg_runs"]
        -
        df["team_b_avg_runs"]
    )

    df[
        "batting_strength_advantage"
    ] = (
        df[
            "batting_strength_difference"
        ] > 0
    ).astype(int)

    # ========================================================
    # 10. WICKET/BOWLING STRENGTH
    # ========================================================

    # Higher average wickets here means more wickets taken/lost
    # according to the historical team feature definition.
    # We retain the original semantics and only compare teams.
    df[
        "wicket_strength_difference"
    ] = (
        df["team_a_avg_wickets"]
        -
        df["team_b_avg_wickets"]
    )

    # ========================================================
    # 11. VENUE FEATURES
    # ========================================================

    df[
        "venue_win_rate_difference"
    ] = (
        df["team_a_venue_win_rate"]
        -
        df["team_b_venue_win_rate"]
    )

    df[
        "venue_sample_difference"
    ] = (
        df[
            "team_a_venue_matches_before"
        ]
        -
        df[
            "team_b_venue_matches_before"
        ]
    )

    df[
        "team_a_venue_reliability"
    ] = reliability(
        df[
            "team_a_venue_matches_before"
        ],
        minimum_sample=5,
    )

    df[
        "team_b_venue_reliability"
    ] = reliability(
        df[
            "team_b_venue_matches_before"
        ],
        minimum_sample=5,
    )

    # Reliability-adjusted venue advantage.
    df[
        "team_a_adjusted_venue_strength"
    ] = (
        df[
            "team_a_venue_win_rate"
        ]
        *
        df[
            "team_a_venue_reliability"
        ]
    )

    df[
        "team_b_adjusted_venue_strength"
    ] = (
        df[
            "team_b_venue_win_rate"
        ]
        *
        df[
            "team_b_venue_reliability"
        ]
    )

    df[
        "adjusted_venue_difference"
    ] = (
        df[
            "team_a_adjusted_venue_strength"
        ]
        -
        df[
            "team_b_adjusted_venue_strength"
        ]
    )

    # ========================================================
    # 12. HEAD-TO-HEAD FEATURES
    # ========================================================

    df[
        "h2h_win_rate_difference"
    ] = (
        df[
            "head_to_head_a_win_rate"
        ]
        -
        df[
            "head_to_head_b_win_rate"
        ]
    )

    df[
        "h2h_sample_reliability"
    ] = reliability(
        df[
            "head_to_head_matches_before"
        ],
        minimum_sample=10,
    )

    df[
        "adjusted_h2h_difference"
    ] = (
        df[
            "h2h_win_rate_difference"
        ]
        *
        df[
            "h2h_sample_reliability"
        ]
    )

    # ========================================================
    # 13. COMBINED TEAM STRENGTH
    # ========================================================

    # A deliberately simple composite signal.
    # It combines overall strength, recent form, batting,
    # venue and H2H without using current-match information.

    df[
        "composite_strength_difference"
    ] = (
        0.30
        * df[
            "overall_strength_difference"
        ]
        +
        0.25
        * df[
            "weighted_form_difference"
        ]
        +
        0.20
        * (
            df[
                "batting_strength_difference"
            ]
            /
            100.0
        )
        +
        0.15
        * (
            df[
                "wicket_strength_difference"
            ]
            /
            10.0
        )
        +
        0.10
        * df[
            "adjusted_venue_difference"
        ]
    )

    df[
        "composite_strength_advantage"
    ] = (
        df[
            "composite_strength_difference"
        ] > 0
    ).astype(int)

    # ========================================================
    # 14. ABSOLUTE DIFFERENCES
    # ========================================================

    df[
        "abs_experience_difference"
    ] = (
        df[
            "experience_difference"
        ].abs()
    )

    df[
        "abs_batting_strength_difference"
    ] = (
        df[
            "batting_strength_difference"
        ].abs()
    )

    df[
        "abs_wicket_strength_difference"
    ] = (
        df[
            "wicket_strength_difference"
        ].abs()
    )

    df[
        "abs_venue_difference"
    ] = (
        df[
            "venue_win_rate_difference"
        ].abs()
    )

    df[
        "abs_h2h_difference"
    ] = (
        df[
            "h2h_win_rate_difference"
        ].abs()
    )

    # ========================================================
    # 15. SANITY CHECKS
    # ========================================================

    numeric_columns = (
        df.select_dtypes(
            include=["number"]
        )
    )

    if numeric_columns.isnull().any().any():

        print(
            "ERROR: V3 contains NULL numeric values."
        )

        sys.exit(1)

    if np.isinf(
        numeric_columns.to_numpy()
    ).any():

        print(
            "ERROR: V3 contains infinite values."
        )

        sys.exit(1)

    print(
        "[PASS] No NULL or infinite values"
    )

    # ========================================================
    # 16. CHECK NEW FEATURES
    # ========================================================

    new_features = [
        "experience_difference",
        "experience_advantage",
        "team_a_experience_reliability",
        "team_b_experience_reliability",
        "experience_reliability_difference",

        "overall_strength_difference",
        "overall_strength_advantage",

        "team_a_weighted_form",
        "team_b_weighted_form",
        "weighted_form_difference",
        "weighted_form_advantage",

        "team_a_recent_momentum",
        "team_b_recent_momentum",
        "recent_momentum_difference",

        "batting_strength_difference",
        "batting_strength_advantage",

        "wicket_strength_difference",

        "venue_win_rate_difference",
        "venue_sample_difference",
        "team_a_venue_reliability",
        "team_b_venue_reliability",

        "team_a_adjusted_venue_strength",
        "team_b_adjusted_venue_strength",
        "adjusted_venue_difference",

        "h2h_win_rate_difference",
        "h2h_sample_reliability",
        "adjusted_h2h_difference",

        "composite_strength_difference",
        "composite_strength_advantage",

        "abs_experience_difference",
        "abs_batting_strength_difference",
        "abs_wicket_strength_difference",
        "abs_venue_difference",
        "abs_h2h_difference",
    ]

    missing_new = [
        column
        for column in new_features
        if column not in df.columns
    ]

    if missing_new:

        print(
            "ERROR: Missing engineered features:"
        )

        for column in missing_new:
            print(f"  {column}")

        sys.exit(1)

    print(
        f"[PASS] Created {len(new_features)} "
        "V3 engineered features"
    )

    # ========================================================
    # 17. RANGE CHECKS
    # ========================================================

    bounded_01 = [
        "team_a_experience_reliability",
        "team_b_experience_reliability",
        "overall_strength_difference",
        "team_a_weighted_form",
        "team_b_weighted_form",
        "team_a_recent_momentum",
        "team_b_recent_momentum",
        "team_a_venue_reliability",
        "team_b_venue_reliability",
        "team_a_adjusted_venue_strength",
        "team_b_adjusted_venue_strength",
        "h2h_sample_reliability",
    ]

    for column in bounded_01:

        minimum = df[column].min()
        maximum = df[column].max()

        if (
            minimum < -1
            or maximum > 1
        ):

            print(
                f"WARNING: {column} "
                f"range={minimum:.4f} -> "
                f"{maximum:.4f}"
            )

    binary_features = [
        "experience_advantage",
        "overall_strength_advantage",
        "weighted_form_advantage",
        "batting_strength_advantage",
        "composite_strength_advantage",
    ]

    for column in binary_features:

        values = set(
            df[column]
            .astype(int)
            .unique()
        )

        if not values.issubset({0, 1}):

            print(
                f"ERROR: {column} "
                f"is not binary: {values}"
            )

            sys.exit(1)

    print(
        "[PASS] Binary feature ranges valid"
    )

    # ========================================================
    # 18. CHRONOLOGY
    # ========================================================

    if not df[
        "match_date"
    ].is_monotonic_increasing:

        print(
            "ERROR: Chronological order changed."
        )

        sys.exit(1)

    print(
        "[PASS] Chronological order preserved"
    )

    # ========================================================
    # 19. SAVE
    # ========================================================

    df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print(
        f"Output rows    : {len(df)}"
    )

    print(
        f"Output columns : {len(df.columns)}"
    )

    print(
        f"New features   : {len(new_features)}"
    )

    print(
        f"Output file    : {OUTPUT_FILE}"
    )

    # ========================================================
    # 20. SUMMARY
    # ========================================================

    print()
    print(
        "V3 FEATURE SUMMARY"
    )

    print("-" * 72)

    summary = [
        (
            "Overall strength",
            "overall_strength_difference",
        ),
        (
            "Weighted recent form",
            "weighted_form_difference",
        ),
        (
            "Batting strength",
            "batting_strength_difference",
        ),
        (
            "Wicket strength",
            "wicket_strength_difference",
        ),
        (
            "Venue strength",
            "adjusted_venue_difference",
        ),
        (
            "Head-to-head",
            "adjusted_h2h_difference",
        ),
        (
            "Composite strength",
            "composite_strength_difference",
        ),
    ]

    for label, column in summary:

        print(
            f"{label:25s} "
            f"mean={df[column].mean():8.4f} "
            f"min={df[column].min():8.4f} "
            f"max={df[column].max():8.4f}"
        )

    print()
    print("=" * 72)
    print(
        "V3 DATASET BUILD COMPLETE"
    )
    print("=" * 72)
    print(
        "PASS: V3 dataset created successfully."
    )


if __name__ == "__main__":
    main()
