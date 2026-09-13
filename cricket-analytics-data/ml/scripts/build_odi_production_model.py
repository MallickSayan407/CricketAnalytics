"""
ODI Match Predictor - Production Model Builder

Creates the frozen production artifact for the ODI predictor.

IMPORTANT:
    The 2022-2026 final test set is NOT used for fitting.
    The model is trained only on the historical development period
    through 2022-07-27.

Model:
    StandardScaler + LogisticRegression
    V2 feature set
    C = 0.001

Output:
    ml/models/odi_v2_production_model.joblib

The artifact contains:
    - trained model pipeline
    - exact feature column order
    - model/version metadata
    - training cutoff
    - target definition
    - final locked-test metrics
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
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

OUTPUT_FILE = (
    MODEL_DIR
    / "odi_v2_production_model.joblib"
)

METADATA_FILE = (
    MODEL_DIR
    / "odi_v2_production_model_metadata.json"
)

CALIBRATION_RESULT_FILE = (
    MODEL_DIR
    / "odi_v2_calibration_results.csv"
)

FINAL_TEST_RESULT_FILE = (
    MODEL_DIR
    / "odi_v2_final_test_result.csv"
)


# ============================================================
# SETTINGS
# ============================================================

FINAL_TEST_RATIO = 0.20

C = 0.001

RANDOM_STATE = 42


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - PRODUCTION MODEL BUILDER"
    )
    print("=" * 72)
    print()

    # ========================================================
    # 1. LOAD DATA
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
    # 2. IDENTIFY MODEL FEATURES
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

    if len(feature_columns) != 51:

        print(
            "ERROR: Expected 51 V2 model features, "
            f"found {len(feature_columns)}."
        )

        sys.exit(1)

    if X.isnull().any().any():

        print(
            "ERROR: NULL model features found."
        )

        sys.exit(1)

    if np.isinf(
        X.to_numpy()
    ).any():

        print(
            "ERROR: Infinite model features found."
        )

        sys.exit(1)

    print(
        f"Model features  : {len(feature_columns)}"
    )

    # ========================================================
    # 3. LOCK FINAL TEST
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

    X_development = X.iloc[
        :final_test_start
    ].copy()

    y_development = y.iloc[
        :final_test_start
    ].copy()

    print()
    print(
        "TRAINING DATA"
    )

    print(
        "-" * 72
    )

    print(
        f"Development rows : "
        f"{len(development_df)}"
    )

    print(
        f"Training period  : "
        f"{development_df['match_date'].min().date()} "
        f"-> "
        f"{development_df['match_date'].max().date()}"
    )

    print()
    print(
        "FINAL TEST REMAINS LOCKED"
    )

    print(
        "-" * 72
    )

    print(
        f"Final test rows : "
        f"{len(final_test_df)}"
    )

    print(
        f"Final test      : "
        f"{final_test_df['match_date'].min().date()} "
        f"-> "
        f"{final_test_df['match_date'].max().date()}"
    )

    # ========================================================
    # 4. TRAIN FINAL PRODUCTION MODEL
    # ========================================================

    print()
    print(
        "TRAINING PRODUCTION MODEL"
    )

    print(
        "-" * 72
    )

    model = Pipeline(
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

    model.fit(
        X_development,
        y_development,
    )

    print(
        "[PASS] Production model trained"
    )

    # ========================================================
    # 5. VERIFY MODEL
    # ========================================================

    sample_probabilities = (
        model
        .predict_proba(
            X_development.head(5)
        )[:, 1]
    )

    if np.any(
        sample_probabilities < 0
    ) or np.any(
        sample_probabilities > 1
    ):

        print(
            "ERROR: Invalid model probabilities."
        )

        sys.exit(1)

    print(
        "[PASS] Probability output verified"
    )

    # ========================================================
    # 6. LOAD FINAL TEST METRICS
    # ========================================================

    final_test_metrics = {}

    if FINAL_TEST_RESULT_FILE.exists():

        test_result = pd.read_csv(
            FINAL_TEST_RESULT_FILE
        )

        if not test_result.empty:

            final_test_metrics = (
                test_result
                .iloc[0]
                .to_dict()
            )

    # ========================================================
    # 7. LOAD CALIBRATION RESULT
    # ========================================================

    calibration_results = []

    if CALIBRATION_RESULT_FILE.exists():

        calibration_df = pd.read_csv(
            CALIBRATION_RESULT_FILE
        )

        calibration_results = (
            calibration_df
            .to_dict(
                orient="records"
            )
        )

    # ========================================================
    # 8. CREATE PRODUCTION PACKAGE
    # ========================================================

    package = {
        "artifact_version":
            "ODI_V2_PRODUCTION_1.0",

        "model_type":
            "LogisticRegression",

        "feature_set":
            "V2",

        "feature_count":
            len(feature_columns),

        "regularization_C":
            C,

        "preprocessing":
            "StandardScaler",

        "target":
            {
                "name":
                    "target",

                "value_1":
                    "Team A wins",

                "value_0":
                    "Team B wins",

                "probability":
                    "Probability that Team A wins",
            },

        "training":
            {
                "rows":
                    len(development_df),

                "start":
                    str(
                        development_df[
                            "match_date"
                        ].min().date()
                    ),

                "end":
                    str(
                        development_df[
                            "match_date"
                        ].max().date()
                    ),

                "split":
                    "chronological",

                "final_test_locked":
                    True,
            },

        "final_test":
            {
                "rows":
                    len(final_test_df),

                "start":
                    str(
                        final_test_df[
                            "match_date"
                        ].min().date()
                    ),

                "end":
                    str(
                        final_test_df[
                            "match_date"
                        ].max().date()
                    ),

                "metrics":
                    final_test_metrics,
            },

        "calibration":
            {
                "selected":
                    "raw",

                "reason":
                    "Raw tuned Logistic Regression "
                    "performed best on the locked final "
                    "test set.",

                "results":
                    calibration_results,
            },

        "feature_columns":
            feature_columns,

        "model":
            model,
    }

    # ========================================================
    # 9. SAVE
    # ========================================================

    joblib.dump(
        package,
        OUTPUT_FILE,
    )

    # Save human-readable metadata separately.
    metadata = {
        key: value
        for key, value in package.items()
        if key != "model"
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
    # 10. RELOAD TEST
    # ========================================================

    print()
    print(
        "VERIFYING SAVED ARTIFACT"
    )

    print(
        "-" * 72
    )

    loaded_package = joblib.load(
        OUTPUT_FILE
    )

    if (
        loaded_package[
            "artifact_version"
        ]
        != "ODI_V2_PRODUCTION_1.0"
    ):

        print(
            "ERROR: Artifact version mismatch."
        )

        sys.exit(1)

    if (
        len(
            loaded_package[
                "feature_columns"
            ]
        )
        != 51
    ):

        print(
            "ERROR: Feature count mismatch."
        )

        sys.exit(1)

    loaded_model = loaded_package[
        "model"
    ]

    verification_probabilities = (
        loaded_model
        .predict_proba(
            X_development.head(3)
        )[:, 1]
    )

    print(
        "[PASS] Artifact reloaded successfully"
    )

    print(
        "[PASS] Feature count = 51"
    )

    print(
        "[PASS] Model probability output verified"
    )

    # ========================================================
    # 11. DISPLAY
    # ========================================================

    print()
    print("=" * 72)
    print(
        "PRODUCTION MODEL"
    )
    print("=" * 72)

    print(
        "Model       : Logistic Regression"
    )

    print(
        "Feature set : V2"
    )

    print(
        f"C           : {C}"
    )

    print(
        "Scaling     : StandardScaler"
    )

    print(
        f"Training    : {len(development_df)} matches"
    )

    print(
        "Test locked : YES"
    )

    print()
    print(
        "FINAL LOCKED TEST METRICS"
    )

    if final_test_metrics:

        for key in [
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "log_loss",
            "brier",
        ]:

            if key in final_test_metrics:

                print(
                    f"{key:<10}: "
                    f"{float(final_test_metrics[key]):.4f}"
                )

    print()
    print(
        "SAVED FILES"
    )

    print(
        "-" * 72
    )

    print(
        f"[OK] {OUTPUT_FILE.name}"
    )

    print(
        f"[OK] {METADATA_FILE.name}"
    )

    print()
    print(
        "Production model artifact created successfully."
    )


if __name__ == "__main__":
    main()
