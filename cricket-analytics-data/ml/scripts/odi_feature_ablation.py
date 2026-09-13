"""
ODI Match Predictor - Feature Ablation Study

Purpose:
    Determine which historical feature groups actually improve ODI
    match prediction.

Method:
    - Same 2,440 matches as V1/V2/V3.
    - Same chronological 80/20 split.
    - Same test period.
    - Logistic Regression is used as the controlled baseline model.
    - Random Forest and XGBoost are intentionally not used here because
      the first question is feature contribution, not algorithm tuning.

Feature groups:
    1. V1 baseline
    2. Historical strength
    3. Historical + recent form
    4. Historical + recent form + venue
    5. Historical + recent form + venue + H2H
    6. V2 engineered features
    7. V3 engineered features

Metrics:
    Accuracy
    Precision
    Recall
    F1
    ROC-AUC
    Log Loss
    Brier Score

Outputs:
    ml/models/odi_feature_ablation_results.csv
    ml/models/odi_feature_ablation_metadata.json
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    log_loss,
    brier_score_loss,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


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

V2_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training_v2.csv"
)

V3_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training_v3.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "models"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

RESULT_FILE = (
    MODEL_DIR
    / "odi_feature_ablation_results.csv"
)

METADATA_FILE = (
    MODEL_DIR
    / "odi_feature_ablation_metadata.json"
)


# ============================================================
# SETTINGS
# ============================================================

TEST_RATIO = 0.20

RANDOM_STATE = 42


# ============================================================
# BASE FEATURE GROUPS
# ============================================================

BASE_FEATURES = [
    "team_a_matches_before",
    "team_b_matches_before",

    "team_a_wins_before",
    "team_b_wins_before",

    "team_a_decided_matches_before",
    "team_b_decided_matches_before",

    "team_a_win_rate",
    "team_b_win_rate",

    "team_a_avg_runs",
    "team_b_avg_runs",

    "team_a_avg_wickets",
    "team_b_avg_wickets",
]


RECENT_FORM_FEATURES = [
    "team_a_last5_win_rate",
    "team_b_last5_win_rate",

    "team_a_last10_win_rate",
    "team_b_last10_win_rate",
]


VENUE_FEATURES = [
    "team_a_venue_matches_before",
    "team_b_venue_matches_before",

    "team_a_venue_win_rate",
    "team_b_venue_win_rate",
]


H2H_FEATURES = [
    "head_to_head_matches_before",

    "head_to_head_a_wins",
    "head_to_head_b_wins",

    "head_to_head_a_win_rate",
    "head_to_head_b_win_rate",
]


V2_ENGINEERED_FEATURES = [
    "matches_before_difference",
    "wins_before_difference",
    "decided_matches_difference",
    "win_rate_difference",
    "last5_win_rate_difference",
    "last10_win_rate_difference",
    "avg_runs_difference",
    "avg_wickets_difference",
    "venue_matches_difference",
    "venue_win_rate_difference",
    "h2h_wins_difference",
    "h2h_win_rate_difference",
    "experience_ratio",
    "win_count_ratio",
    "avg_runs_ratio",
    "avg_wickets_ratio",
    "abs_win_rate_difference",
    "abs_last5_difference",
    "abs_last10_difference",
    "abs_avg_runs_difference",
    "abs_avg_wickets_difference",
    "team_a_win_rate_advantage",
    "team_a_recent5_advantage",
    "team_a_recent10_advantage",
    "team_a_venue_advantage",
    "team_a_h2h_advantage",
]


V3_ENGINEERED_FEATURES = [
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


# ============================================================
# DATASET DEFINITIONS
# ============================================================

EXPERIMENTS = {
    "01_V1_Baseline": BASE_FEATURES,

    "02_Strength": (
        BASE_FEATURES
    ),

    "03_Strength_Plus_Recent_Form": (
        BASE_FEATURES
        + RECENT_FORM_FEATURES
    ),

    "04_Strength_Form_Plus_Venue": (
        BASE_FEATURES
        + RECENT_FORM_FEATURES
        + VENUE_FEATURES
    ),

    "05_Strength_Form_Venue_Plus_H2H": (
        BASE_FEATURES
        + RECENT_FORM_FEATURES
        + VENUE_FEATURES
        + H2H_FEATURES
    ),

    "06_V2_All_Engineered": (
        BASE_FEATURES
        + RECENT_FORM_FEATURES
        + VENUE_FEATURES
        + H2H_FEATURES
        + V2_ENGINEERED_FEATURES
    ),

    "07_V3_All_Engineered": (
        BASE_FEATURES
        + RECENT_FORM_FEATURES
        + VENUE_FEATURES
        + H2H_FEATURES
        + V3_ENGINEERED_FEATURES
    ),
}


# ============================================================
# HELPERS
# ============================================================

def load_dataset(path):

    if not path.exists():

        print(
            f"ERROR: Dataset not found: {path}"
        )

        sys.exit(1)

    df = pd.read_csv(
        path
    )

    df["match_date"] = pd.to_datetime(
        df["match_date"]
    )

    df = (
        df
        .sort_values(
            [
                "match_date",
                "match_id",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return df


def train_and_evaluate(
    df,
    feature_columns,
):

    missing = [
        column
        for column in feature_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Missing features: "
            + ", ".join(missing)
        )

    X = df[
        feature_columns
    ]

    y = df[
        "target"
    ].astype(int)

    if X.isnull().any().any():

        raise ValueError(
            "Feature set contains NULL values."
        )

    if np.isinf(
        X.to_numpy()
    ).any():

        raise ValueError(
            "Feature set contains infinite values."
        )

    split_index = int(
        len(df)
        * (1 - TEST_RATIO)
    )

    X_train = X.iloc[
        :split_index
    ]

    X_test = X.iloc[
        split_index:
    ]

    y_train = y.iloc[
        :split_index
    ]

    y_test = y.iloc[
        split_index:
    ]

    model = Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )

    model.fit(
        X_train,
        y_train,
    )

    probabilities = (
        model
        .predict_proba(
            X_test
        )[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    return {
        "accuracy": accuracy_score(
            y_test,
            predictions,
        ),
        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_test,
            probabilities,
        ),
        "log_loss": log_loss(
            y_test,
            probabilities,
            labels=[0, 1],
        ),
        "brier": brier_score_loss(
            y_test,
            probabilities,
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - FEATURE ABLATION STUDY"
    )
    print("=" * 72)
    print()

    # ========================================================
    # 1. LOAD ALL DATASETS
    # ========================================================

    v1 = load_dataset(
        V1_FILE
    )

    v2 = load_dataset(
        V2_FILE
    )

    v3 = load_dataset(
        V3_FILE
    )

    print(
        f"V1 rows: {len(v1)}"
    )

    print(
        f"V2 rows: {len(v2)}"
    )

    print(
        f"V3 rows: {len(v3)}"
    )

    if not (
        len(v1)
        == len(v2)
        == len(v3)
    ):

        print(
            "ERROR: Dataset row counts differ."
        )

        sys.exit(1)

    # ========================================================
    # 2. VERIFY MATCH IDs
    # ========================================================

    if not (
        v1["match_id"].equals(
            v2["match_id"]
        )
        and
        v1["match_id"].equals(
            v3["match_id"]
        )
    ):

        print(
            "ERROR: Match IDs differ between versions."
        )

        sys.exit(1)

    print(
        "[PASS] V1/V2/V3 match IDs identical"
    )

    # ========================================================
    # 3. VERIFY TARGET
    # ========================================================

    if not (
        v1["target"].equals(
            v2["target"]
        )
        and
        v1["target"].equals(
            v3["target"]
        )
    ):

        print(
            "ERROR: Target differs between versions."
        )

        sys.exit(1)

    print(
        "[PASS] V1/V2/V3 targets identical"
    )

    # ========================================================
    # 4. EXPERIMENTS
    # ========================================================

    results = []

    for experiment_name, features in EXPERIMENTS.items():

        # Select the dataset containing all required columns.
        if experiment_name.startswith(
            "06_"
        ):

            dataset = v2

        elif experiment_name.startswith(
            "07_"
        ):

            dataset = v3

        else:

            dataset = v1

        print()
        print(
            f"Running {experiment_name}..."
        )

        metrics = train_and_evaluate(
            dataset,
            features,
        )

        row = {
            "experiment": experiment_name,
            "feature_count": len(features),
            **metrics,
        }

        results.append(
            row
        )

        print(
            f"  Features : {len(features)}"
        )

        print(
            f"  Accuracy : "
            f"{metrics['accuracy']:.4f}"
        )

        print(
            f"  Precision: "
            f"{metrics['precision']:.4f}"
        )

        print(
            f"  Recall   : "
            f"{metrics['recall']:.4f}"
        )

        print(
            f"  F1       : "
            f"{metrics['f1']:.4f}"
        )

        print(
            f"  ROC-AUC  : "
            f"{metrics['roc_auc']:.4f}"
        )

        print(
            f"  Log Loss : "
            f"{metrics['log_loss']:.4f}"
        )

        print(
            f"  Brier    : "
            f"{metrics['brier']:.4f}"
        )

    # ========================================================
    # 5. RESULTS
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    # ========================================================
    # 6. DELTAS FROM BASELINE
    # ========================================================

    baseline = (
        results_df.iloc[0]
    )

    results_df[
        "accuracy_delta_vs_v1"
    ] = (
        results_df["accuracy"]
        - baseline["accuracy"]
    )

    results_df[
        "roc_auc_delta_vs_v1"
    ] = (
        results_df["roc_auc"]
        - baseline["roc_auc"]
    )

    results_df[
        "log_loss_delta_vs_v1"
    ] = (
        results_df["log_loss"]
        - baseline["log_loss"]
    )

    results_df[
        "brier_delta_vs_v1"
    ] = (
        results_df["brier"]
        - baseline["brier"]
    )

    # ========================================================
    # 7. SAVE RESULTS
    # ========================================================

    results_df.to_csv(
        RESULT_FILE,
        index=False,
    )

    # ========================================================
    # 8. BEST EXPERIMENTS
    # ========================================================

    best_auc = (
        results_df
        .loc[
            results_df[
                "roc_auc"
            ].idxmax()
        ]
    )

    best_log_loss = (
        results_df
        .loc[
            results_df[
                "log_loss"
            ].idxmin()
        ]
    )

    best_brier = (
        results_df
        .loc[
            results_df[
                "brier"
            ].idxmin()
        ]
    )

    best_accuracy = (
        results_df
        .loc[
            results_df[
                "accuracy"
            ].idxmax()
        ]
    )

    # ========================================================
    # 9. METADATA
    # ========================================================

    metadata = {
        "method":
            "chronological_80_20_logistic_regression",

        "rows":
            int(len(v1)),

        "train_rows":
            int(len(v1) * (1 - TEST_RATIO)),

        "test_rows":
            int(len(v1) * TEST_RATIO),

        "train_start":
            str(
                v1[
                    "match_date"
                ].min().date()
            ),

        "train_end":
            str(
                v1[
                    "match_date"
                ].iloc[
                    int(len(v1) * (1 - TEST_RATIO)) - 1
                ].date()
            ),

        "test_start":
            str(
                v1[
                    "match_date"
                ].iloc[
                    int(len(v1) * (1 - TEST_RATIO))
                ].date()
            ),

        "test_end":
            str(
                v1[
                    "match_date"
                ].max().date()
            ),

        "experiments":
            list(
                EXPERIMENTS.keys()
            ),

        "best_roc_auc_experiment":
            str(
                best_auc["experiment"]
            ),

        "best_log_loss_experiment":
            str(
                best_log_loss["experiment"]
            ),

        "best_brier_experiment":
            str(
                best_brier["experiment"]
            ),

        "best_accuracy_experiment":
            str(
                best_accuracy["experiment"]
            ),
    }

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    # ========================================================
    # 10. DISPLAY RESULTS
    # ========================================================

    print()
    print("=" * 72)
    print(
        "FEATURE ABLATION RESULTS"
    )
    print("=" * 72)

    print(
        results_df[
            [
                "experiment",
                "feature_count",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "roc_auc",
                "log_loss",
                "brier",
            ]
        ].to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}",
        )
    )

    # ========================================================
    # 11. BEST RESULTS
    # ========================================================

    print()
    print(
        "BEST BY METRIC"
    )

    print("-" * 72)

    print(
        f"Accuracy : "
        f"{best_accuracy['experiment']} "
        f"({best_accuracy['accuracy']:.4f})"
    )

    print(
        f"ROC-AUC  : "
        f"{best_auc['experiment']} "
        f"({best_auc['roc_auc']:.4f})"
    )

    print(
        f"Log Loss : "
        f"{best_log_loss['experiment']} "
        f"({best_log_loss['log_loss']:.4f})"
    )

    print(
        f"Brier    : "
        f"{best_brier['experiment']} "
        f"({best_brier['brier']:.4f})"
    )

    # ========================================================
    # 12. OUTPUT
    # ========================================================

    print()
    print("=" * 72)
    print(
        "SAVED FILES"
    )
    print("=" * 72)

    print(
        f"[OK] {RESULT_FILE.name}"
    )

    print(
        f"[OK] {METADATA_FILE.name}"
    )

    print()
    print(
        "Feature ablation study complete."
    )


if __name__ == "__main__":
    main()
