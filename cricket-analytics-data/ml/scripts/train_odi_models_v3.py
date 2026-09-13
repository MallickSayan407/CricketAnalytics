"""
ODI Match Predictor - V3 Model Training

Trains the audited V3 ODI dataset using the same chronological
80/20 split used for V1 and V2.

Models:
    Logistic Regression
    Random Forest
    XGBoost

Outputs are saved with V3-specific filenames and V1/V2 files
are never overwritten.
"""

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    log_loss,
    brier_score_loss,
    confusion_matrix,
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


# ============================================================
# OUTPUT FILES
# ============================================================

V3_LOGISTIC_FILE = (
    MODEL_DIR
    / "odi_v3_logistic_regression.joblib"
)

V3_RF_FILE = (
    MODEL_DIR
    / "odi_v3_random_forest.joblib"
)

V3_XGB_FILE = (
    MODEL_DIR
    / "odi_v3_xgboost.joblib"
)

V3_BEST_FILE = (
    MODEL_DIR
    / "odi_v3_best_model.joblib"
)

V3_COMPARISON_FILE = (
    MODEL_DIR
    / "odi_v3_model_comparison.csv"
)

ALL_VERSION_COMPARISON_FILE = (
    MODEL_DIR
    / "odi_v1_v2_v3_comparison.csv"
)

V3_IMPORTANCE_FILE = (
    MODEL_DIR
    / "odi_v3_feature_importance.csv"
)

V3_CONFUSION_FILE = (
    MODEL_DIR
    / "odi_v3_confusion_matrices.png"
)

V3_METADATA_FILE = (
    MODEL_DIR
    / "odi_v3_model_metadata.json"
)


# ============================================================
# SETTINGS
# ============================================================

TEST_RATIO = 0.20

RANDOM_STATE = 42


# ============================================================
# XGBOOST
# ============================================================

try:

    from xgboost import XGBClassifier

    XGBOOST_AVAILABLE = True

except ImportError:

    XGBOOST_AVAILABLE = False

    print(
        "WARNING: XGBoost is not installed."
    )

    print(
        "Install with:"
    )

    print(
        "python -m pip install xgboost"
    )


# ============================================================
# EVALUATION
# ============================================================

def evaluate_model(
    model,
    X_test,
    y_test,
):

    probabilities = (
        model
        .predict_proba(X_test)[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    metrics = {
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

    matrix = confusion_matrix(
        y_test,
        predictions,
    )

    return metrics, matrix


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - V3 MODEL TRAINING"
    )
    print("=" * 72)
    print()

    # ========================================================
    # 1. LOAD DATASET
    # ========================================================

    if not DATASET_FILE.exists():

        print(
            "ERROR: V3 dataset not found:"
        )

        print(DATASET_FILE)

        sys.exit(1)

    df = pd.read_csv(
        DATASET_FILE
    )

    print(
        f"Dataset rows    : {len(df)}"
    )

    print(
        f"Dataset columns : {len(df.columns)}"
    )

    print()

    if df.empty:

        print(
            "ERROR: Dataset is empty."
        )

        sys.exit(1)

    # ========================================================
    # 2. VALIDATE BASIC DATA
    # ========================================================

    required_columns = [
        "match_id",
        "match_date",
        "target",
    ]

    for column in required_columns:

        if column not in df.columns:

            print(
                f"ERROR: Required column missing: "
                f"{column}"
            )

            sys.exit(1)

    if df["match_id"].duplicated().any():

        print(
            "ERROR: Duplicate match IDs detected."
        )

        sys.exit(1)

    if df["target"].isnull().any():

        print(
            "ERROR: NULL target values."
        )

        sys.exit(1)

    # ========================================================
    # 3. CHRONOLOGICAL ORDER
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

    if not df[
        "match_date"
    ].is_monotonic_increasing:

        print(
            "ERROR: Dataset is not chronological."
        )

        sys.exit(1)

    # ========================================================
    # 4. MODEL FEATURES
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

    if not feature_columns:

        print(
            "ERROR: No model features found."
        )

        sys.exit(1)

    non_numeric = [
        column
        for column in feature_columns
        if not pd.api.types.is_numeric_dtype(
            df[column]
        )
    ]

    if non_numeric:

        print(
            "ERROR: Non-numeric model features:"
        )

        for column in non_numeric:
            print(f"  {column}")

        sys.exit(1)

    X_all = df[
        feature_columns
    ]

    y_all = df[
        "target"
    ].astype(int)

    if X_all.isnull().any().any():

        print(
            "ERROR: Model features contain NULL values."
        )

        sys.exit(1)

    if np.isinf(
        X_all.to_numpy()
    ).any():

        print(
            "ERROR: Model features contain infinity."
        )

        sys.exit(1)

    print(
        f"Model features  : {len(feature_columns)}"
    )

    print()

    # ========================================================
    # 5. CHRONOLOGICAL 80/20 SPLIT
    # ========================================================

    split_index = int(
        len(df)
        * (1 - TEST_RATIO)
    )

    train_df = df.iloc[
        :split_index
    ].copy()

    test_df = df.iloc[
        split_index:
    ].copy()

    X_train = train_df[
        feature_columns
    ]

    y_train = train_df[
        "target"
    ].astype(int)

    X_test = test_df[
        feature_columns
    ]

    y_test = test_df[
        "target"
    ].astype(int)

    print(
        "CHRONOLOGICAL SPLIT"
    )

    print(
        "-" * 72
    )

    print(
        f"Training rows : {len(train_df)}"
    )

    print(
        f"Testing rows  : {len(test_df)}"
    )

    print(
        f"Train period  : "
        f"{train_df['match_date'].min().date()} "
        f"-> "
        f"{train_df['match_date'].max().date()}"
    )

    print(
        f"Test period   : "
        f"{test_df['match_date'].min().date()} "
        f"-> "
        f"{test_df['match_date'].max().date()}"
    )

    print()

    # ========================================================
    # 6. TARGET DISTRIBUTION
    # ========================================================

    print(
        "TARGET DISTRIBUTION"
    )

    print(
        "-" * 72
    )

    train_counts = (
        y_train
        .value_counts()
        .sort_index()
    )

    test_counts = (
        y_test
        .value_counts()
        .sort_index()
    )

    print(
        f"Training Team B (0): "
        f"{train_counts.get(0, 0)} "
        f"({train_counts.get(0, 0) / len(y_train) * 100:.2f}%)"
    )

    print(
        f"Training Team A (1): "
        f"{train_counts.get(1, 0)} "
        f"({train_counts.get(1, 0) / len(y_train) * 100:.2f}%)"
    )

    print()

    print(
        f"Testing Team B (0): "
        f"{test_counts.get(0, 0)} "
        f"({test_counts.get(0, 0) / len(y_test) * 100:.2f}%)"
    )

    print(
        f"Testing Team A (1): "
        f"{test_counts.get(1, 0)} "
        f"({test_counts.get(1, 0) / len(y_test) * 100:.2f}%)"
    )

    print()

    # ========================================================
    # 7. MODELS
    # ========================================================

    models = {}

    models[
        "Logistic Regression"
    ] = Pipeline(
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

    models[
        "Random Forest"
    ] = RandomForestClassifier(
        n_estimators=500,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
        min_samples_leaf=2,
    )

    if XGBOOST_AVAILABLE:

        models[
            "XGBoost"
        ] = XGBClassifier(
            n_estimators=400,
            max_depth=4,
            learning_rate=0.03,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="binary:logistic",
            eval_metric="logloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

    # ========================================================
    # 8. TRAIN
    # ========================================================

    print("=" * 72)
    print(
        "MODEL TRAINING"
    )
    print("=" * 72)
    print()

    results = []

    trained_models = {}

    confusion_matrices = {}

    for model_name, model in models.items():

        print(
            f"Training {model_name}..."
        )

        model.fit(
            X_train,
            y_train,
        )

        metrics, matrix = evaluate_model(
            model,
            X_test,
            y_test,
        )

        trained_models[
            model_name
        ] = model

        confusion_matrices[
            model_name
        ] = matrix

        results.append(
            {
                "model": model_name,
                **metrics,
            }
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

        print()

    # ========================================================
    # 9. RESULTS
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    results_df = (
        results_df
        .sort_values(
            [
                "roc_auc",
                "accuracy",
                "f1",
            ],
            ascending=False,
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # 10. SAVE INDIVIDUAL MODELS
    # ========================================================

    joblib.dump(
        trained_models[
            "Logistic Regression"
        ],
        V3_LOGISTIC_FILE,
    )

    joblib.dump(
        trained_models[
            "Random Forest"
        ],
        V3_RF_FILE,
    )

    if "XGBoost" in trained_models:

        joblib.dump(
            trained_models[
                "XGBoost"
            ],
            V3_XGB_FILE,
        )

    # ========================================================
    # 11. BEST MODEL
    # ========================================================

    best_model_name = (
        results_df.iloc[0]["model"]
    )

    best_model = trained_models[
        best_model_name
    ]

    joblib.dump(
        best_model,
        V3_BEST_FILE,
    )

    # ========================================================
    # 12. SAVE V3 RESULTS
    # ========================================================

    results_df.to_csv(
        V3_COMPARISON_FILE,
        index=False,
    )

    # ========================================================
    # 13. V1 + V2 + V3 COMPARISON
    # ========================================================

    version_tables = []

    # ---------------- V1 ----------------

    v1_file = (
        MODEL_DIR
        / "odi_model_comparison.csv"
    )

    if v1_file.exists():

        v1_df = pd.read_csv(
            v1_file
        )

        v1_df[
            "version"
        ] = "V1"

        version_tables.append(
            v1_df
        )

    # ---------------- V2 ----------------

    v2_file = (
        MODEL_DIR
        / "odi_v2_model_comparison.csv"
    )

    if v2_file.exists():

        v2_df = pd.read_csv(
            v2_file
        )

        v2_df[
            "version"
        ] = "V2"

        version_tables.append(
            v2_df
        )

    # ---------------- V3 ----------------

    v3_df = results_df.copy()

    v3_df[
        "version"
    ] = "V3"

    version_tables.append(
        v3_df
    )

    comparison_columns = [
        "version",
        "model",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "log_loss",
        "brier",
    ]

    comparison_tables = []

    for table in version_tables:

        available = [
            column
            for column in comparison_columns
            if column in table.columns
        ]

        comparison_tables.append(
            table[available]
        )

    all_comparison = pd.concat(
        comparison_tables,
        ignore_index=True,
    )

    all_comparison.to_csv(
        ALL_VERSION_COMPARISON_FILE,
        index=False,
    )

    # ========================================================
    # 14. FEATURE IMPORTANCE
    # ========================================================

    if (
        best_model_name
        == "Logistic Regression"
    ):

        classifier = (
            best_model
            .named_steps[
                "classifier"
            ]
        )

        coefficients = (
            classifier.coef_[0]
        )

        importance_df = pd.DataFrame(
            {
                "feature": feature_columns,
                "coefficient": coefficients,
                "absolute_importance":
                    np.abs(coefficients),
            }
        )

        importance_df = (
            importance_df
            .sort_values(
                "absolute_importance",
                ascending=False,
            )
            .reset_index(
                drop=True
            )
        )

    else:

        importance_df = pd.DataFrame(
            {
                "feature": feature_columns,
                "importance":
                    best_model.feature_importances_,
            }
        )

        importance_df = (
            importance_df
            .sort_values(
                "importance",
                ascending=False,
            )
            .reset_index(
                drop=True
            )
        )

    importance_df.to_csv(
        V3_IMPORTANCE_FILE,
        index=False,
    )

    # ========================================================
    # 15. CONFUSION MATRICES
    # ========================================================

    try:

        import matplotlib.pyplot as plt

        model_names = list(
            confusion_matrices.keys()
        )

        fig, axes = plt.subplots(
            1,
            len(model_names),
            figsize=(
                5 * len(model_names),
                4,
            ),
        )

        if len(model_names) == 1:
            axes = [axes]

        for axis, model_name in zip(
            axes,
            model_names,
        ):

            matrix = (
                confusion_matrices[
                    model_name
                ]
            )

            axis.imshow(
                matrix
            )

            axis.set_title(
                model_name
            )

            axis.set_xlabel(
                "Predicted"
            )

            axis.set_ylabel(
                "Actual"
            )

            axis.set_xticks(
                [0, 1]
            )

            axis.set_yticks(
                [0, 1]
            )

            for i in range(2):

                for j in range(2):

                    axis.text(
                        j,
                        i,
                        matrix[i, j],
                        ha="center",
                        va="center",
                    )

        plt.tight_layout()

        plt.savefig(
            V3_CONFUSION_FILE,
            dpi=150,
        )

        plt.close()

    except Exception as exc:

        print(
            "WARNING: Could not create "
            "confusion matrix image:"
        )

        print(exc)

    # ========================================================
    # 16. METADATA
    # ========================================================

    metadata = {
        "dataset":
            "odi_match_training_v3.csv",

        "rows":
            int(len(df)),

        "columns":
            int(len(df.columns)),

        "feature_count":
            int(len(feature_columns)),

        "train_rows":
            int(len(train_df)),

        "test_rows":
            int(len(test_df)),

        "train_start":
            str(
                train_df[
                    "match_date"
                ].min().date()
            ),

        "train_end":
            str(
                train_df[
                    "match_date"
                ].max().date()
            ),

        "test_start":
            str(
                test_df[
                    "match_date"
                ].min().date()
            ),

        "test_end":
            str(
                test_df[
                    "match_date"
                ].max().date()
            ),

        "split_type":
            "chronological",

        "test_ratio":
            TEST_RATIO,

        "random_state":
            RANDOM_STATE,

        "best_model":
            best_model_name,

        "models_trained":
            list(
                trained_models.keys()
            ),

        "feature_columns":
            feature_columns,

        "results":
            results_df.to_dict(
                orient="records"
            ),
    }

    with open(
        V3_METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    # ========================================================
    # 17. DISPLAY RESULTS
    # ========================================================

    print()
    print("=" * 72)
    print(
        "V3 MODEL COMPARISON"
    )
    print("=" * 72)

    display_columns = [
        "model",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "log_loss",
        "brier",
    ]

    print(
        results_df[
            display_columns
        ].to_string(
            index=False,
            float_format=lambda value:
                f"{value:.4f}",
        )
    )

    print()
    print(
        f"BEST V3 MODEL: "
        f"{best_model_name}"
    )

    print()
    print(
        "TOP 15 V3 FEATURES"
    )

    print("-" * 72)

    print(
        importance_df
        .head(15)
        .to_string(
            index=False
        )
    )

    # ========================================================
    # 18. THREE-VERSION SUMMARY
    # ========================================================

    print()
    print("=" * 72)
    print(
        "V1 vs V2 vs V3 - LOGISTIC REGRESSION"
    )
    print("=" * 72)

    logistic_rows = (
        all_comparison[
            all_comparison[
                "model"
            ]
            .eq("Logistic Regression")
        ]
    )

    print(
        logistic_rows[
            [
                "version",
                "accuracy",
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
    # 19. SAVED FILES
    # ========================================================

    print()
    print("=" * 72)
    print(
        "SAVED FILES"
    )
    print("=" * 72)

    output_files = [
        V3_LOGISTIC_FILE,
        V3_RF_FILE,
        V3_XGB_FILE,
        V3_BEST_FILE,
        V3_COMPARISON_FILE,
        ALL_VERSION_COMPARISON_FILE,
        V3_IMPORTANCE_FILE,
        V3_CONFUSION_FILE,
        V3_METADATA_FILE,
    ]

    for file in output_files:

        if file.exists():

            print(
                f"[OK] {file.name}"
            )

        else:

            print(
                f"[NOT CREATED] "
                f"{file.name}"
            )

    print()
    print(
        "V3 training complete."
    )


if __name__ == "__main__":
    main()
