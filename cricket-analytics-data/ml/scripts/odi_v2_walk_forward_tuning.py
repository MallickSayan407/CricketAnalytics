"""
ODI Match Predictor - Walk-Forward Hyperparameter Tuning (V2)

Purpose:
    Tune the V2 Logistic Regression model without touching the final
    2022-2026 test set.

Validation:
    Expanding-window chronological validation inside the original
    1,952-match training period.

Final test:
    488 matches from 2022-07-31 onward remain completely untouched.

Hyperparameters:
    Logistic Regression C values.

Outputs:
    ml/models/odi_v2_walk_forward_tuning.csv
    ml/models/odi_v2_walk_forward_metadata.json
    ml/models/odi_v2_tuned_logistic_regression.joblib
    ml/models/odi_v2_final_test_result.csv
"""

import json
import sys
from pathlib import Path

import joblib
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

DATASET_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training_v2.csv"
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

TUNING_FILE = (
    MODEL_DIR
    / "odi_v2_walk_forward_tuning.csv"
)

METADATA_FILE = (
    MODEL_DIR
    / "odi_v2_walk_forward_metadata.json"
)

TUNED_MODEL_FILE = (
    MODEL_DIR
    / "odi_v2_tuned_logistic_regression.joblib"
)

FINAL_TEST_FILE = (
    MODEL_DIR
    / "odi_v2_final_test_result.csv"
)


# ============================================================
# SETTINGS
# ============================================================

FINAL_TEST_RATIO = 0.20

RANDOM_STATE = 42

C_VALUES = [
    0.001,
    0.01,
    0.1,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    50.0,
    100.0,
]


# ============================================================
# WALK-FORWARD FOLDS
# ============================================================
#
# All folds are strictly chronological.
#
# Fold 1:
#   train 1-60% of pre-test data
#   validate next 10%
#
# Fold 2:
#   train 1-70%
#   validate next 10%
#
# Fold 3:
#   train 1-80%
#   validate next 10%
#
# Fold 4:
#   train 1-90%
#   validate final 10% of the training period
#
# The final 20% of the complete dataset is never touched here.
# ============================================================

VALIDATION_FRACTIONS = [
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.00),
]


# ============================================================
# HELPERS
# ============================================================

def make_model(C):

    return Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=C,
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def evaluate(
    model,
    X,
    y,
):

    probabilities = (
        model
        .predict_proba(X)[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    return {
        "accuracy": accuracy_score(
            y,
            predictions,
        ),
        "precision": precision_score(
            y,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y,
            predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y,
            predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y,
            probabilities,
        ),
        "log_loss": log_loss(
            y,
            probabilities,
            labels=[0, 1],
        ),
        "brier": brier_score_loss(
            y,
            probabilities,
        ),
    }


def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - WALK-FORWARD HYPERPARAMETER TUNING"
    )
    print("=" * 72)
    print()

    # ========================================================
    # 1. LOAD
    # ========================================================

    if not DATASET_FILE.exists():

        print(
            "ERROR: V2 dataset not found:"
        )

        print(DATASET_FILE)

        sys.exit(1)

    df = pd.read_csv(
        DATASET_FILE
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

    print(
        f"Dataset rows    : {len(df)}"
    )

    print(
        f"Dataset columns : {len(df.columns)}"
    )

    # ========================================================
    # 2. FEATURES
    # ========================================================

    excluded_columns = {
        "target",
        "match_id",
        "external_id",
        "match_date",
        "team_a_id",
        "team_b_id",
        "team_a",
        "team_b",
        "venue_id",
        "venue",
        "result",
    }

    feature_columns = [
        column
        for column in df.columns
        if column not in excluded_columns
    ]

    X = df[
        feature_columns
    ]

    y = df[
        "target"
    ].astype(int)

    if X.isnull().any().any():

        print(
            "ERROR: NULL model features."
        )

        sys.exit(1)

    if np.isinf(
        X.to_numpy()
    ).any():

        print(
            "ERROR: Infinite model features."
        )

        sys.exit(1)

    print(
        f"Model features  : {len(feature_columns)}"
    )

    # ========================================================
    # 3. FINAL TEST SPLIT
    # ========================================================

    final_test_start = int(
        len(df)
        * (1 - FINAL_TEST_RATIO)
    )

    development_df = df.iloc[
        :final_test_start
    ].copy()

    final_test_df = df.iloc[
        final_test_start:
    ].copy()

    X_dev = X.iloc[
        :final_test_start
    ]

    y_dev = y.iloc[
        :final_test_start
    ]

    X_final = X.iloc[
        final_test_start:
    ]

    y_final = y.iloc[
        final_test_start:
    ]

    print()
    print(
        "FINAL TEST SET (LOCKED)"
    )

    print(
        "-" * 72
    )

    print(
        f"Development rows : "
        f"{len(development_df)}"
    )

    print(
        f"Final test rows  : "
        f"{len(final_test_df)}"
    )

    print(
        f"Development      : "
        f"{development_df['match_date'].min().date()} "
        f"-> "
        f"{development_df['match_date'].max().date()}"
    )

    print(
        f"Final test       : "
        f"{final_test_df['match_date'].min().date()} "
        f"-> "
        f"{final_test_df['match_date'].max().date()}"
    )

    # ========================================================
    # 4. WALK-FORWARD TUNING
    # ========================================================

    print()
    print(
        "WALK-FORWARD VALIDATION"
    )

    print(
        "-" * 72
    )

    fold_indices = []

    for fold_number, (
        train_fraction,
        validation_fraction,
    ) in enumerate(
        VALIDATION_FRACTIONS,
        start=1,
    ):

        train_end = int(
            len(development_df)
            * train_fraction
        )

        validation_end = int(
            len(development_df)
            * validation_fraction
        )

        train_start = 0
        validation_start = train_end

        if (
            train_end <= train_start
            or validation_end <= validation_start
        ):

            print(
                "ERROR: Invalid fold boundaries."
            )

            sys.exit(1)

        fold_indices.append(
            (
                fold_number,
                train_start,
                train_end,
                validation_start,
                validation_end,
            )
        )

        print(
            f"Fold {fold_number}: "
            f"train {train_start}:{train_end} "
            f"({train_end - train_start}) | "
            f"validate {validation_start}:{validation_end} "
            f"({validation_end - validation_start})"
        )

    # ========================================================
    # 5. TUNE C
    # ========================================================

    all_rows = []

    for C in C_VALUES:

        fold_results = []

        for (
            fold_number,
            train_start,
            train_end,
            validation_start,
            validation_end,
        ) in fold_indices:

            X_train = X_dev.iloc[
                train_start:train_end
            ]

            y_train = y_dev.iloc[
                train_start:train_end
            ]

            X_validation = X_dev.iloc[
                validation_start:validation_end
            ]

            y_validation = y_dev.iloc[
                validation_start:validation_end
            ]

            model = make_model(
                C
            )

            model.fit(
                X_train,
                y_train,
            )

            metrics = evaluate(
                model,
                X_validation,
                y_validation,
            )

            fold_results.append(
                metrics
            )

            all_rows.append(
                {
                    "C": C,
                    "fold": fold_number,
                    "train_rows":
                        len(X_train),
                    "validation_rows":
                        len(X_validation),
                    "validation_start":
                        str(
                            development_df
                            .iloc[
                                validation_start
                            ][
                                "match_date"
                            ].date()
                        ),
                    "validation_end":
                        str(
                            development_df
                            .iloc[
                                validation_end - 1
                            ][
                                "match_date"
                            ].date()
                        ),
                    **metrics,
                }
            )

        mean_metrics = {
            key:
                float(
                    np.mean(
                        [
                            result[key]
                            for result in fold_results
                        ]
                    )
                )
            for key in fold_results[0]
        }

        print()
        print(
            f"C = {C}"
        )

        print(
            f"  Mean Accuracy : "
            f"{mean_metrics['accuracy']:.4f}"
        )

        print(
            f"  Mean ROC-AUC  : "
            f"{mean_metrics['roc_auc']:.4f}"
        )

        print(
            f"  Mean Log Loss : "
            f"{mean_metrics['log_loss']:.4f}"
        )

        print(
            f"  Mean Brier    : "
            f"{mean_metrics['brier']:.4f}"
        )

    fold_df = pd.DataFrame(
        all_rows
    )

    # ========================================================
    # 6. AGGREGATE
    # ========================================================

    aggregate_df = (
        fold_df
        .groupby("C")
        .agg(
            mean_accuracy=(
                "accuracy",
                "mean",
            ),
            mean_precision=(
                "precision",
                "mean",
            ),
            mean_recall=(
                "recall",
                "mean",
            ),
            mean_f1=(
                "f1",
                "mean",
            ),
            mean_roc_auc=(
                "roc_auc",
                "mean",
            ),
            mean_log_loss=(
                "log_loss",
                "mean",
            ),
            mean_brier=(
                "brier",
                "mean",
            ),
        )
        .reset_index()
    )

    # Choose using ROC-AUC first, then probability quality.
    aggregate_df = (
        aggregate_df
        .sort_values(
            [
                "mean_roc_auc",
                "mean_log_loss",
                "mean_brier",
            ],
            ascending=[
                False,
                True,
                True,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    best_C = float(
        aggregate_df.iloc[0]["C"]
    )

    # ========================================================
    # 7. DISPLAY AGGREGATE RESULTS
    # ========================================================

    print()
    print("=" * 72)
    print(
        "WALK-FORWARD TUNING RESULTS"
    )
    print("=" * 72)

    print(
        aggregate_df.to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}",
        )
    )

    print()
    print(
        f"SELECTED C: {best_C}"
    )

    print(
        "Selection priority: "
        "mean ROC-AUC → mean Log Loss → mean Brier"
    )

    # ========================================================
    # 8. FIT SELECTED MODEL ON ALL DEVELOPMENT DATA
    # ========================================================

    tuned_model = make_model(
        best_C
    )

    tuned_model.fit(
        X_dev,
        y_dev,
    )

    # ========================================================
    # 9. FINAL LOCKED TEST
    # ========================================================

    final_metrics = evaluate(
        tuned_model,
        X_final,
        y_final,
    )

    # ========================================================
    # 10. SAVE MODEL
    # ========================================================

    joblib.dump(
        tuned_model,
        TUNED_MODEL_FILE,
    )

    # ========================================================
    # 11. SAVE TUNING RESULTS
    # ========================================================

    aggregate_df.to_csv(
        TUNING_FILE,
        index=False,
    )

    # ========================================================
    # 12. SAVE FINAL RESULT
    # ========================================================

    final_result = pd.DataFrame(
        [
            {
                "model":
                    "V2 Tuned Logistic Regression",
                "C":
                    best_C,
                **final_metrics,
            }
        ]
    )

    final_result.to_csv(
        FINAL_TEST_FILE,
        index=False,
    )

    # ========================================================
    # 13. METADATA
    # ========================================================

    metadata = {
        "dataset":
            "odi_match_training_v2.csv",

        "method":
            "expanding_window_walk_forward_validation",

        "final_test_locked":
            True,

        "final_test_ratio":
            FINAL_TEST_RATIO,

        "random_state":
            RANDOM_STATE,

        "feature_count":
            len(feature_columns),

        "development_rows":
            len(development_df),

        "final_test_rows":
            len(final_test_df),

        "development_start":
            str(
                development_df[
                    "match_date"
                ].min().date()
            ),

        "development_end":
            str(
                development_df[
                    "match_date"
                ].max().date()
            ),

        "final_test_start":
            str(
                final_test_df[
                    "match_date"
                ].min().date()
            ),

        "final_test_end":
            str(
                final_test_df[
                    "match_date"
                ].max().date()
            ),

        "C_values":
            C_VALUES,

        "selected_C":
            best_C,

        "selection_priority":
            [
                "mean_roc_auc",
                "mean_log_loss",
                "mean_brier",
            ],

        "final_test_metrics":
            final_metrics,
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
    # 14. FINAL DISPLAY
    # ========================================================

    print()
    print("=" * 72)
    print(
        "FINAL LOCKED TEST RESULT"
    )
    print("=" * 72)

    print(
        f"Selected C : {best_C}"
    )

    print(
        f"Accuracy   : "
        f"{final_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision  : "
        f"{final_metrics['precision']:.4f}"
    )

    print(
        f"Recall     : "
        f"{final_metrics['recall']:.4f}"
    )

    print(
        f"F1         : "
        f"{final_metrics['f1']:.4f}"
    )

    print(
        f"ROC-AUC    : "
        f"{final_metrics['roc_auc']:.4f}"
    )

    print(
        f"Log Loss   : "
        f"{final_metrics['log_loss']:.4f}"
    )

    print(
        f"Brier      : "
        f"{final_metrics['brier']:.4f}"
    )

    print()
    print("=" * 72)
    print(
        "SAVED FILES"
    )
    print("=" * 72)

    for path in [
        TUNING_FILE,
        METADATA_FILE,
        TUNED_MODEL_FILE,
        FINAL_TEST_FILE,
    ]:

        if path.exists():
            print(
                f"[OK] {path.name}"
            )
        else:
            print(
                f"[NOT CREATED] {path.name}"
            )

    print()
    print(
        "Walk-forward tuning complete."
    )


if __name__ == "__main__":
    main()
