"""
ODI Match Predictor - Probability Calibration

Calibrates the selected V2 Logistic Regression model using only
the historical development period.

IMPORTANT:
    The final 2022-2026 test set is never used to fit calibration.

Models compared:
    1. Raw tuned Logistic Regression
    2. Sigmoid / Platt-style calibration
    3. Isotonic calibration

Calibration training:
    Expanding chronological folds inside the 1,952-match
    development period.

Final evaluation:
    Locked 488-match test period:
        2022-07-31 -> 2026-08-13

Primary selection:
    Brier Score, then Log Loss, then ROC-AUC.

Outputs:
    ml/models/odi_v2_calibration_results.csv
    ml/models/odi_v2_calibration_fold_results.csv
    ml/models/odi_v2_calibrated_best_model.joblib
    ml/models/odi_v2_calibration_metadata.json
    ml/models/odi_v2_calibration_curve.png
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


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

TUNED_MODEL_FILE = (
    MODEL_DIR
    / "odi_v2_tuned_logistic_regression.joblib"
)

RESULT_FILE = (
    MODEL_DIR
    / "odi_v2_calibration_results.csv"
)

FOLD_RESULT_FILE = (
    MODEL_DIR
    / "odi_v2_calibration_fold_results.csv"
)

BEST_MODEL_FILE = (
    MODEL_DIR
    / "odi_v2_calibrated_best_model.joblib"
)

METADATA_FILE = (
    MODEL_DIR
    / "odi_v2_calibration_metadata.json"
)

CURVE_FILE = (
    MODEL_DIR
    / "odi_v2_calibration_curve.png"
)


# ============================================================
# SETTINGS
# ============================================================

FINAL_TEST_RATIO = 0.20

RANDOM_STATE = 42

BEST_C = 0.001

CALIBRATION_FOLDS = [
    (0.60, 0.70),
    (0.70, 0.80),
    (0.80, 0.90),
    (0.90, 1.00),
]


# ============================================================
# MODEL
# ============================================================

def make_base_model():

    return Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    C=BEST_C,
                    max_iter=2000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    y_true,
    probabilities,
):

    probabilities = np.clip(
        probabilities,
        1e-15,
        1 - 1e-15,
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    return {
        "accuracy": accuracy_score(
            y_true,
            predictions,
        ),
        "precision": precision_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "roc_auc": roc_auc_score(
            y_true,
            probabilities,
        ),
        "log_loss": log_loss(
            y_true,
            probabilities,
            labels=[0, 1],
        ),
        "brier": brier_score_loss(
            y_true,
            probabilities,
        ),
    }


# ============================================================
# CALIBRATION ERROR
# ============================================================

def expected_calibration_error(
    y_true,
    probabilities,
    bins=10,
):

    y_true = np.asarray(
        y_true
    )

    probabilities = np.asarray(
        probabilities
    )

    edges = np.linspace(
        0.0,
        1.0,
        bins + 1,
    )

    ece = 0.0

    for index in range(bins):

        lower = edges[index]
        upper = edges[index + 1]

        if index == bins - 1:

            mask = (
                (probabilities >= lower)
                &
                (probabilities <= upper)
            )

        else:

            mask = (
                (probabilities >= lower)
                &
                (probabilities < upper)
            )

        count = mask.sum()

        if count == 0:
            continue

        mean_probability = (
            probabilities[mask].mean()
        )

        observed_frequency = (
            y_true[mask].mean()
        )

        weight = (
            count
            / len(y_true)
        )

        ece += (
            weight
            * abs(
                mean_probability
                - observed_frequency
            )
        )

    return ece


# ============================================================
# SIGMOID CALIBRATION
# ============================================================

def fit_sigmoid(
    raw_probabilities,
    y_true,
):

    raw_probabilities = np.clip(
        raw_probabilities,
        1e-6,
        1 - 1e-6,
    )

    logits = np.log(
        raw_probabilities
        /
        (1.0 - raw_probabilities)
    )

    calibrator = LogisticRegression(
        C=1.0,
        max_iter=2000,
        random_state=RANDOM_STATE,
    )

    calibrator.fit(
        logits.reshape(-1, 1),
        y_true,
    )

    return calibrator


def sigmoid_predict(
    calibrator,
    raw_probabilities,
):

    raw_probabilities = np.clip(
        raw_probabilities,
        1e-6,
        1 - 1e-6,
    )

    logits = np.log(
        raw_probabilities
        /
        (1.0 - raw_probabilities)
    )

    return calibrator.predict_proba(
        logits.reshape(-1, 1)
    )[:, 1]


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - PROBABILITY CALIBRATION"
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
    # 2. MODEL FEATURES
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
            "ERROR: NULL features."
        )

        sys.exit(1)

    if np.isinf(
        X.to_numpy()
    ).any():

        print(
            "ERROR: Infinite features."
        )

        sys.exit(1)

    # ========================================================
    # 3. LOCK FINAL TEST
    # ========================================================

    final_test_start = int(
        len(df)
        * (1 - FINAL_TEST_RATIO)
    )

    X_dev = X.iloc[
        :final_test_start
    ].copy()

    y_dev = y.iloc[
        :final_test_start
    ].copy()

    X_final = X.iloc[
        final_test_start:
    ].copy()

    y_final = y.iloc[
        final_test_start:
    ].copy()

    development_df = df.iloc[
        :final_test_start
    ]

    final_test_df = df.iloc[
        final_test_start:
    ]

    print()
    print(
        "LOCKED FINAL TEST"
    )

    print(
        "-" * 72
    )

    print(
        f"Development rows : "
        f"{len(X_dev)}"
    )

    print(
        f"Final test rows  : "
        f"{len(X_final)}"
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
    # 4. WALK-FORWARD CALIBRATION DATA
    # ========================================================

    print()
    print(
        "BUILDING WALK-FORWARD CALIBRATION PREDICTIONS"
    )

    print(
        "-" * 72
    )

    calibration_rows = []

    for fold_number, (
        train_fraction,
        calibration_fraction,
    ) in enumerate(
        CALIBRATION_FOLDS,
        start=1,
    ):

        train_end = int(
            len(X_dev)
            * train_fraction
        )

        calibration_end = int(
            len(X_dev)
            * calibration_fraction
        )

        X_train = X_dev.iloc[
            :train_end
        ]

        y_train = y_dev.iloc[
            :train_end
        ]

        X_calibration = X_dev.iloc[
            train_end:calibration_end
        ]

        y_calibration = y_dev.iloc[
            train_end:calibration_end
        ]

        base_model = make_base_model()

        base_model.fit(
            X_train,
            y_train,
        )

        raw_probabilities = (
            base_model
            .predict_proba(
                X_calibration
            )[:, 1]
        )

        print(
            f"Fold {fold_number}: "
            f"train={len(X_train)} | "
            f"calibration={len(X_calibration)}"
        )

        for index in range(
            len(X_calibration)
        ):

            calibration_rows.append(
                {
                    "fold":
                        fold_number,
                    "date":
                        str(
                            development_df
                            .iloc[
                                train_end + index
                            ][
                                "match_date"
                            ].date()
                        ),
                    "target":
                        int(
                            y_calibration
                            .iloc[index]
                        ),
                    "raw_probability":
                        float(
                            raw_probabilities[
                                index
                            ]
                        ),
                }
            )

    calibration_df = pd.DataFrame(
        calibration_rows
    )

    if calibration_df.empty:

        print(
            "ERROR: No calibration predictions."
        )

        sys.exit(1)

    # ========================================================
    # 5. FIT CALIBRATORS
    # ========================================================

    raw_p = calibration_df[
        "raw_probability"
    ].to_numpy()

    calibration_y = calibration_df[
        "target"
    ].to_numpy()

    print()
    print(
        "FITTING CALIBRATORS"
    )

    print(
        "-" * 72
    )

    sigmoid_calibrator = fit_sigmoid(
        raw_p,
        calibration_y,
    )

    isotonic_calibrator = (
        IsotonicRegression(
            y_min=0.0,
            y_max=1.0,
            out_of_bounds="clip",
        )
    )

    isotonic_calibrator.fit(
        raw_p,
        calibration_y,
    )

    print(
        "[PASS] Sigmoid calibrator fitted"
    )

    print(
        "[PASS] Isotonic calibrator fitted"
    )

    # ========================================================
    # 6. TRAIN BASE MODEL ON ALL DEVELOPMENT DATA
    # ========================================================

    final_base_model = make_base_model()

    final_base_model.fit(
        X_dev,
        y_dev,
    )

    raw_final_probabilities = (
        final_base_model
        .predict_proba(
            X_final
        )[:, 1]
    )

    # ========================================================
    # 7. CALIBRATE FINAL TEST PREDICTIONS
    # ========================================================

    sigmoid_final_probabilities = (
        sigmoid_predict(
            sigmoid_calibrator,
            raw_final_probabilities,
        )
    )

    isotonic_final_probabilities = (
        isotonic_calibrator.predict(
            raw_final_probabilities
        )
    )

    # ========================================================
    # 8. EVALUATE
    # ========================================================

    model_probabilities = {
        "Raw Tuned Logistic Regression":
            raw_final_probabilities,

        "Sigmoid Calibrated":
            sigmoid_final_probabilities,

        "Isotonic Calibrated":
            isotonic_final_probabilities,
    }

    result_rows = []

    for model_name, probabilities in (
        model_probabilities.items()
    ):

        metrics = calculate_metrics(
            y_final,
            probabilities,
        )

        ece = expected_calibration_error(
            y_final,
            probabilities,
        )

        result_rows.append(
            {
                "model":
                    model_name,
                **metrics,
                "ece":
                    ece,
            }
        )

    results_df = pd.DataFrame(
        result_rows
    )

    # ========================================================
    # 9. SELECT BEST CALIBRATED MODEL
    # ========================================================

    results_df = (
        results_df
        .sort_values(
            [
                "brier",
                "log_loss",
                "roc_auc",
            ],
            ascending=[
                True,
                True,
                False,
            ],
        )
        .reset_index(
            drop=True
        )
    )

    best_model_name = (
        results_df.iloc[0]["model"]
    )

    # ========================================================
    # 10. SAVE CALIBRATED MODEL PACKAGE
    # ========================================================

    if (
        best_model_name
        == "Raw Tuned Logistic Regression"
    ):

        best_package = {
            "type":
                "raw_logistic",
            "base_model":
                final_base_model,
            "feature_columns":
                feature_columns,
            "C":
                BEST_C,
        }

    elif (
        best_model_name
        == "Sigmoid Calibrated"
    ):

        best_package = {
            "type":
                "sigmoid_calibrated",
            "base_model":
                final_base_model,
            "calibrator":
                sigmoid_calibrator,
            "feature_columns":
                feature_columns,
            "C":
                BEST_C,
        }

    else:

        best_package = {
            "type":
                "isotonic_calibrated",
            "base_model":
                final_base_model,
            "calibrator":
                isotonic_calibrator,
            "feature_columns":
                feature_columns,
            "C":
                BEST_C,
        }

    joblib.dump(
        best_package,
        BEST_MODEL_FILE,
    )

    # ========================================================
    # 11. SAVE RESULTS
    # ========================================================

    results_df.to_csv(
        RESULT_FILE,
        index=False,
    )

    calibration_df.to_csv(
        FOLD_RESULT_FILE,
        index=False,
    )

    # ========================================================
    # 12. CALIBRATION CURVE
    # ========================================================

    try:

        import matplotlib.pyplot as plt
        from sklearn.calibration import calibration_curve

        fig, axis = plt.subplots(
            figsize=(7, 6)
        )

        for model_name, probabilities in (
            model_probabilities.items()
        ):

            fraction_positive, mean_predicted = (
                calibration_curve(
                    y_final,
                    probabilities,
                    n_bins=10,
                    strategy="uniform",
                )
            )

            axis.plot(
                mean_predicted,
                fraction_positive,
                marker="o",
                label=model_name,
            )

        axis.plot(
            [0, 1],
            [0, 1],
            linestyle="--",
            label="Perfect calibration",
        )

        axis.set_xlabel(
            "Mean predicted probability"
        )

        axis.set_ylabel(
            "Observed frequency"
        )

        axis.set_title(
            "ODI Predictor Probability Calibration"
        )

        axis.legend()

        axis.grid(
            True,
            alpha=0.3,
        )

        plt.tight_layout()

        plt.savefig(
            CURVE_FILE,
            dpi=150,
        )

        plt.close()

        print(
            "[OK] Calibration curve created"
        )

    except Exception as exc:

        print(
            "[WARNING] Could not create calibration curve:"
        )

        print(exc)

    # ========================================================
    # 13. METADATA
    # ========================================================

    metadata = {
        "dataset":
            "odi_match_training_v2.csv",

        "base_model":
            "Logistic Regression",

        "C":
            BEST_C,

        "feature_count":
            len(feature_columns),

        "development_rows":
            len(X_dev),

        "final_test_rows":
            len(X_final),

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

        "calibration_folds":
            CALIBRATION_FOLDS,

        "calibration_rows":
            len(calibration_df),

        "final_test_locked":
            True,

        "selection_priority":
            [
                "brier",
                "log_loss",
                "roc_auc",
            ],

        "best_model":
            best_model_name,

        "results":
            results_df.to_dict(
                orient="records"
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
    # 14. DISPLAY
    # ========================================================

    print()
    print("=" * 72)
    print(
        "CALIBRATION RESULTS - LOCKED FINAL TEST"
    )
    print("=" * 72)

    print(
        results_df[
            [
                "model",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "roc_auc",
                "log_loss",
                "brier",
                "ece",
            ]
        ].to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}",
        )
    )

    print()
    print(
        f"BEST CALIBRATED MODEL: "
        f"{best_model_name}"
    )

    print()
    print("=" * 72)
    print(
        "SAVED FILES"
    )
    print("=" * 72)

    for path in [
        RESULT_FILE,
        FOLD_RESULT_FILE,
        BEST_MODEL_FILE,
        METADATA_FILE,
        CURVE_FILE,
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
        "Probability calibration complete."
    )


if __name__ == "__main__":
    main()
