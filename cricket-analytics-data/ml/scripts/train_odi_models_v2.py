"""
ODI Match Predictor - V2 Model Training

Purpose:
    Train the V2 ODI match prediction dataset using the same
    chronological methodology used for V1.

Models:
    1. Logistic Regression
    2. Random Forest
    3. XGBoost

Evaluation:
    Accuracy
    Precision
    Recall
    F1
    ROC-AUC
    Log Loss
    Brier Score

Important:
    - Uses chronological 80/20 split.
    - Does NOT randomly shuffle the dataset.
    - Does NOT overwrite V1 model files.
    - Saves V2 models separately.
    - Produces V1 vs V2 comparison files.
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


# ============================================================
# OUTPUT FILES
# ============================================================

V2_LOGISTIC_FILE = (
    MODEL_DIR / "odi_v2_logistic_regression.joblib"
)

V2_RF_FILE = (
    MODEL_DIR / "odi_v2_random_forest.joblib"
)

V2_XGB_FILE = (
    MODEL_DIR / "odi_v2_xgboost.joblib"
)

V2_BEST_FILE = (
    MODEL_DIR / "odi_v2_best_model.joblib"
)

V2_COMPARISON_FILE = (
    MODEL_DIR / "odi_v2_model_comparison.csv"
)

V1_V2_COMPARISON_FILE = (
    MODEL_DIR / "odi_v1_vs_v2_comparison.csv"
)

V2_IMPORTANCE_FILE = (
    MODEL_DIR / "odi_v2_feature_importance.csv"
)

V2_CONFUSION_FILE = (
    MODEL_DIR / "odi_v2_confusion_matrices.png"
)

V2_METADATA_FILE = (
    MODEL_DIR / "odi_v2_model_metadata.json"
)


# ============================================================
# MODEL SETTINGS
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
# METRIC FUNCTION
# ============================================================

def evaluate_model(
    model,
    X_test,
    y_test,
):

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

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

    cm = confusion_matrix(
        y_test,
        predictions,
    )

    return metrics, cm


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print(
        "ODI MATCH PREDICTOR - V2 MODEL TRAINING"
    )
    print("=" * 72)
    print()

    # ========================================================
    # 1. CHECK DATASET
    # ========================================================

    if not DATASET_FILE.exists():

        print(
            "ERROR: V2 dataset not found:"
        )

        print(DATASET_FILE)

        sys.exit(1)

    # ========================================================
    # 2. LOAD DATA
    # ========================================================

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

    # ========================================================
    # 3. BASIC VALIDATION
    # ========================================================

    if df.empty:

        print(
            "ERROR: Dataset is empty."
        )

        sys.exit(1)

    if "target" not in df.columns:

        print(
            "ERROR: target column missing."
        )

        sys.exit(1)

    if df["target"].isnull().any():

        print(
            "ERROR: target contains NULL values."
        )

        sys.exit(1)

    if df["match_id"].duplicated().any():

        print(
            "ERROR: duplicate match IDs detected."
        )

        sys.exit(1)

    # ========================================================
    # 4. SORT CHRONOLOGICALLY
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
    # 5. DEFINE FEATURES
    # ========================================================

    excluded_columns = [
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
    ]

    feature_columns = [
        column
        for column in df.columns
        if column not in excluded_columns
    ]

    # Make sure all model features are numeric.

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

    # ========================================================
    # 6. CHECK NULL / INFINITY
    # ========================================================

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

    # ========================================================
    # 7. CHRONOLOGICAL SPLIT
    # ========================================================

    split_index = int(
        len(df) * (1 - TEST_RATIO)
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
    # 8. TARGET DISTRIBUTION
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
    # 9. MODEL DEFINITIONS
    # ========================================================

    models = {}

    # Logistic Regression with scaling.
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

    # Random Forest.
    models[
        "Random Forest"
    ] = RandomForestClassifier(
        n_estimators=500,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        class_weight="balanced",
        min_samples_leaf=2,
    )

    # XGBoost.
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
    # 10. TRAIN MODELS
    # ========================================================

    results = []

    confusion_matrices = {}

    trained_models = {}

    print(
        "=" * 72
    )

    print(
        "MODEL TRAINING"
    )

    print(
        "=" * 72
    )

    print()

    for model_name, model in models.items():

        print(
            f"Training {model_name}..."
        )

        model.fit(
            X_train,
            y_train,
        )

        metrics, cm = evaluate_model(
            model,
            X_test,
            y_test,
        )

        trained_models[
            model_name
        ] = model

        confusion_matrices[
            model_name
        ] = cm

        row = {
            "model": model_name,
            **metrics,
        }

        results.append(
            row
        )

        print(
            f"  Accuracy : {metrics['accuracy']:.4f}"
        )

        print(
            f"  Precision: {metrics['precision']:.4f}"
        )

        print(
            f"  Recall   : {metrics['recall']:.4f}"
        )

        print(
            f"  F1       : {metrics['f1']:.4f}"
        )

        print(
            f"  ROC-AUC  : {metrics['roc_auc']:.4f}"
        )

        print(
            f"  Log Loss : {metrics['log_loss']:.4f}"
        )

        print(
            f"  Brier    : {metrics['brier']:.4f}"
        )

        print()

    # ========================================================
    # 11. RESULTS DATAFRAME
    # ========================================================

    results_df = pd.DataFrame(
        results
    )

    # Higher is better for these.
    results_df = results_df.sort_values(
        [
            "roc_auc",
            "accuracy",
            "f1",
        ],
        ascending=False,
    ).reset_index(
        drop=True
    )

    # ========================================================
    # 12. SAVE MODELS
    # ========================================================

    trained_models[
        "Logistic Regression"
    ] and joblib.dump(
        trained_models[
            "Logistic Regression"
        ],
        V2_LOGISTIC_FILE,
    )

    joblib.dump(
        trained_models[
            "Random Forest"
        ],
        V2_RF_FILE,
    )

    if (
        "XGBoost"
        in trained_models
    ):

        joblib.dump(
            trained_models[
                "XGBoost"
            ],
            V2_XGB_FILE,
        )

    # ========================================================
    # 13. SELECT BEST MODEL
    # ========================================================

    best_model_name = (
        results_df.iloc[0]["model"]
    )

    best_model = trained_models[
        best_model_name
    ]

    joblib.dump(
        best_model,
        V2_BEST_FILE,
    )

    # ========================================================
    # 14. SAVE MODEL COMPARISON
    # ========================================================

    results_df.to_csv(
        V2_COMPARISON_FILE,
        index=False,
    )

    # ========================================================
    # 15. V1 VS V2 COMPARISON
    # ========================================================

    v1_comparison_file = (
        MODEL_DIR
        / "odi_model_comparison.csv"
    )

    if v1_comparison_file.exists():

        v1_df = pd.read_csv(
            v1_comparison_file
        )

        v1_df = v1_df.rename(
            columns={
                "accuracy": "accuracy",
                "precision": "precision",
                "recall": "recall",
                "f1": "f1",
                "roc_auc": "roc_auc",
                "log_loss": "log_loss",
                "brier": "brier",
            }
        )

        v1_df[
            "version"
        ] = "V1"

        results_for_comparison = (
            results_df.copy()
        )

        results_for_comparison[
            "version"
        ] = "V2"

        common_columns = [
            "model",
            "accuracy",
            "precision",
            "recall",
            "f1",
            "roc_auc",
            "log_loss",
            "brier",
            "version",
        ]

        v1_available = [
            column
            for column in common_columns
            if column in v1_df.columns
        ]

        v2_available = [
            column
            for column in common_columns
            if column in results_for_comparison.columns
        ]

        v1_clean = v1_df[
            v1_available
        ].copy()

        v2_clean = results_for_comparison[
            v2_available
        ].copy()

        comparison_df = pd.concat(
            [
                v1_clean,
                v2_clean,
            ],
            ignore_index=True,
        )

        comparison_df.to_csv(
            V1_V2_COMPARISON_FILE,
            index=False,
        )

    # ========================================================
    # 16. FEATURE IMPORTANCE
    # ========================================================

    importance_model = best_model

    if (
        best_model_name
        == "Logistic Regression"
    ):

        classifier = (
            importance_model
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
                "absolute_importance": np.abs(
                    coefficients
                ),
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

        importances = (
            importance_model
            .feature_importances_
        )

        importance_df = pd.DataFrame(
            {
                "feature": feature_columns,
                "importance": importances,
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
        V2_IMPORTANCE_FILE,
        index=False,
    )

    # ========================================================
    # 17. CONFUSION MATRIX PLOT
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

            cm = confusion_matrices[
                model_name
            ]

            axis.imshow(cm)

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
                        cm[i, j],
                        ha="center",
                        va="center",
                    )

        plt.tight_layout()

        plt.savefig(
            V2_CONFUSION_FILE,
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
    # 18. METADATA
    # ========================================================

    metadata = {
        "dataset": "odi_match_training_v2.csv",
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "feature_count": int(
            len(feature_columns)
        ),
        "train_rows": int(
            len(train_df)
        ),
        "test_rows": int(
            len(test_df)
        ),
        "train_start": str(
            train_df[
                "match_date"
            ].min().date()
        ),
        "train_end": str(
            train_df[
                "match_date"
            ].max().date()
        ),
        "test_start": str(
            test_df[
                "match_date"
            ].min().date()
        ),
        "test_end": str(
            test_df[
                "match_date"
            ].max().date()
        ),
        "test_ratio": TEST_RATIO,
        "random_state": RANDOM_STATE,
        "split_type": "chronological",
        "best_model": best_model_name,
        "models_trained": list(
            trained_models.keys()
        ),
        "feature_columns": feature_columns,
        "results": results_df.to_dict(
            orient="records"
        ),
    }

    with open(
        V2_METADATA_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            metadata,
            file,
            indent=2,
        )

    # ========================================================
    # 19. DISPLAY FINAL RESULTS
    # ========================================================

    print()
    print(
        "=" * 72
    )

    print(
        "V2 MODEL COMPARISON"
    )

    print(
        "=" * 72
    )

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
        f"BEST V2 MODEL: {best_model_name}"
    )

    print()

    # ========================================================
    # 20. TOP FEATURES
    # ========================================================

    print(
        "TOP 15 V2 FEATURES"
    )

    print(
        "-" * 72
    )

    print(
        importance_df
        .head(15)
        .to_string(
            index=False
        )
    )

    # ========================================================
    # 21. FINAL FILES
    # ========================================================

    print()
    print(
        "=" * 72
    )

    print(
        "SAVED FILES"
    )

    print(
        "=" * 72
    )

    files = [
        V2_LOGISTIC_FILE,
        V2_RF_FILE,
        V2_XGB_FILE,
        V2_BEST_FILE,
        V2_COMPARISON_FILE,
        V1_V2_COMPARISON_FILE,
        V2_IMPORTANCE_FILE,
        V2_CONFUSION_FILE,
        V2_METADATA_FILE,
    ]

    for file in files:

        if file.exists():

            print(
                f"[OK] {file.name}"
            )

        else:

            print(
                f"[NOT CREATED] {file.name}"
            )

    print()
    print(
        "V2 training complete."
    )


if __name__ == "__main__":
    main()
