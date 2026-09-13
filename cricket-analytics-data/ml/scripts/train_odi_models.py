"""
Train and compare ODI Match Prediction models.

Input:
    D:\CricketAnalytics\cricket-analytics-data\ml\datasets\odi_match_training.csv

Output:
    ml\models\odi_logistic_regression.joblib
    ml\models\odi_random_forest.joblib
    ml\models\odi_xgboost.joblib
    ml\models\odi_best_model.joblib
    ml\models\odi_model_metadata.json
    ml\models\odi_feature_importance.csv
    ml\models\odi_confusion_matrices.png
    ml\models\odi_model_comparison.csv

IMPORTANT:
- Uses a chronological 80/20 train/test split.
- Never randomly shuffles matches.
- Team names/IDs, venue, dates, match IDs, and target are NOT model features.
- All features were generated before each match, so current-match leakage is avoided.
"""

import json
import sys
import warnings
from pathlib import Path

try:
    import joblib
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt

    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
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

    from xgboost import XGBClassifier

except ImportError as exc:
    print()
    print("ERROR: A required ML package is missing:")
    print(exc)
    print()
    print("Run inside your .venv:")
    print("python -m pip install pandas numpy scikit-learn xgboost joblib matplotlib")
    sys.exit(1)


warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"D:\CricketAnalytics\cricket-analytics-data")

DATASET_FILE = (
    BASE_DIR
    / "ml"
    / "datasets"
    / "odi_match_training.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "models"
)

TRAIN_RATIO = 0.80
RANDOM_STATE = 42


# These are the ONLY columns used as ML features.
FEATURE_COLUMNS = [
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
]

TARGET_COLUMN = "target"


# ============================================================
# DATA LOADING
# ============================================================

def load_dataset():
    if not DATASET_FILE.exists():
        print(f"ERROR: Dataset not found:\n{DATASET_FILE}")
        sys.exit(1)

    df = pd.read_csv(DATASET_FILE)

    print(f"Dataset rows    : {len(df)}")
    print(f"Dataset columns : {len(df.columns)}")

    missing = [
        c for c in FEATURE_COLUMNS + [TARGET_COLUMN]
        if c not in df.columns
    ]

    if missing:
        print("ERROR: Missing required columns:")
        for column in missing:
            print(f"  - {column}")
        sys.exit(1)

    # Explicit chronological ordering check.
    df["match_date"] = pd.to_datetime(df["match_date"])

    sorted_df = df.sort_values(
        ["match_date", "match_id"]
    ).reset_index(drop=True)

    if not df.reset_index(drop=True).equals(sorted_df):
        print("WARNING: Dataset wasn't perfectly sorted.")
        print("Sorting chronologically before splitting.")

    df = sorted_df

    return df


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

def chronological_split(df):
    split_index = int(len(df) * TRAIN_RATIO)

    train_df = df.iloc[:split_index].copy()
    test_df = df.iloc[split_index:].copy()

    return train_df, test_df


# ============================================================
# PREPROCESSING
# ============================================================

def make_logistic_pipeline():
    """
    Logistic Regression benefits from feature scaling.
    Median imputation protects the pipeline if future datasets
    contain missing numerical values.
    """

    preprocessor = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    return Pipeline([
        ("preprocessor", preprocessor),
        (
            "model",
            LogisticRegression(
                max_iter=2000,
                random_state=RANDOM_STATE,
            ),
        ),
    ])


def make_random_forest():
    return Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "model",
            RandomForestClassifier(
                n_estimators=500,
                max_depth=None,
                min_samples_leaf=2,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
    ])


def make_xgboost():
    return Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "model",
            XGBClassifier(
                n_estimators=500,
                max_depth=4,
                learning_rate=0.03,
                subsample=0.85,
                colsample_bytree=0.85,
                min_child_weight=3,
                reg_lambda=1.0,
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=RANDOM_STATE,
                n_jobs=-1,
            ),
        ),
    ])


# ============================================================
# METRICS
# ============================================================

def evaluate_model(model, x_test, y_test):
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
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
        ),
        "brier_score": brier_score_loss(
            y_test,
            probabilities,
        ),
    }

    return metrics, predictions, probabilities


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

def extract_feature_importance(model, feature_columns):
    """
    Extracts importance from:
      - Logistic Regression coefficients
      - Random Forest feature_importances_
      - XGBoost feature_importances_
    """

    final_model = model.named_steps["model"]

    if isinstance(final_model, LogisticRegression):
        values = np.abs(
            final_model.coef_[0]
        )

    elif hasattr(final_model, "feature_importances_"):
        values = final_model.feature_importances_

    else:
        return pd.DataFrame()

    result = pd.DataFrame({
        "feature": feature_columns,
        "importance": values,
    })

    result = result.sort_values(
        "importance",
        ascending=False,
    ).reset_index(drop=True)

    return result


# ============================================================
# SAVE CONFUSION MATRIX FIGURE
# ============================================================

def save_confusion_matrices(results, y_test):
    model_names = list(results.keys())

    fig, axes = plt.subplots(
        1,
        len(model_names),
        figsize=(15, 4.5),
    )

    if len(model_names) == 1:
        axes = [axes]

    for ax, name in zip(axes, model_names):
        predictions = results[name]["predictions"]

        cm = confusion_matrix(
            y_test,
            predictions,
        )

        ax.imshow(cm)

        ax.set_title(name)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("Actual")

        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])

        for i in range(2):
            for j in range(2):
                ax.text(
                    j,
                    i,
                    str(cm[i, j]),
                    ha="center",
                    va="center",
                )

    plt.tight_layout()

    output = MODEL_DIR / "odi_confusion_matrices.png"
    plt.savefig(output, dpi=150)
    plt.close()

    return output


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 72)
    print("ODI MATCH PREDICTOR - MODEL TRAINING")
    print("=" * 72)
    print()

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = load_dataset()

    print()
    print("CHRONOLOGICAL SPLIT")
    print("-" * 72)

    train_df, test_df = chronological_split(df)

    print(f"Training rows : {len(train_df)}")
    print(f"Testing rows  : {len(test_df)}")
    print(
        f"Train period  : "
        f"{train_df['match_date'].min().date()} -> "
        f"{train_df['match_date'].max().date()}"
    )
    print(
        f"Test period   : "
        f"{test_df['match_date'].min().date()} -> "
        f"{test_df['match_date'].max().date()}"
    )

    # Check that test data is genuinely later than training data.
    if test_df["match_date"].min() < train_df["match_date"].max():
        print()
        print(
            "WARNING: Train/test dates overlap. "
            "This can happen because multiple matches occur on the same date."
        )

    x_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_COLUMN].astype(int)

    x_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_COLUMN].astype(int)

    print()
    print("TARGET DISTRIBUTION")
    print("-" * 72)
    print(
        f"Train Team B wins (0): "
        f"{(y_train == 0).sum()} "
        f"({(y_train == 0).mean() * 100:.2f}%)"
    )
    print(
        f"Train Team A wins (1): "
        f"{(y_train == 1).sum()} "
        f"({(y_train == 1).mean() * 100:.2f}%)"
    )
    print(
        f"Test Team B wins (0):  "
        f"{(y_test == 0).sum()} "
        f"({(y_test == 0).mean() * 100:.2f}%)"
    )
    print(
        f"Test Team A wins (1):  "
        f"{(y_test == 1).sum()} "
        f"({(y_test == 1).mean() * 100:.2f}%)"
    )

    models = {
        "Logistic Regression": make_logistic_pipeline(),
        "Random Forest": make_random_forest(),
        "XGBoost": make_xgboost(),
    }

    results = {}
    comparison_rows = []

    print()
    print("=" * 72)
    print("TRAINING MODELS")
    print("=" * 72)

    for name, model in models.items():
        print()
        print(f"Training {name}...")

        model.fit(
            x_train,
            y_train,
        )

        metrics, predictions, probabilities = evaluate_model(
            model,
            x_test,
            y_test,
        )

        results[name] = {
            "model": model,
            "predictions": predictions,
            "probabilities": probabilities,
            "metrics": metrics,
        }

        comparison_rows.append({
            "model": name,
            **metrics,
        })

        safe_name = (
            name.lower()
            .replace(" ", "_")
        )

        output_model = (
            MODEL_DIR
            / f"odi_{safe_name}.joblib"
        )

        joblib.dump(
            model,
            output_model,
        )

        print(f"Saved: {output_model}")

    comparison = pd.DataFrame(
        comparison_rows
    )

    # ---------------------------------------------------------
    # Model selection
    # ---------------------------------------------------------
    #
    # For a probability-based sports predictor, ROC-AUC and
    # Log Loss are especially useful. We rank primarily by
    # ROC-AUC, then lower Log Loss.
    #

    comparison = comparison.sort_values(
        ["roc_auc", "log_loss"],
        ascending=[False, True],
    ).reset_index(drop=True)

    best_name = comparison.iloc[0]["model"]
    best_model = results[best_name]["model"]

    best_model_file = (
        MODEL_DIR
        / "odi_best_model.joblib"
    )

    joblib.dump(
        best_model,
        best_model_file,
    )

    # ---------------------------------------------------------
    # Save comparison
    # ---------------------------------------------------------

    comparison_file = (
        MODEL_DIR
        / "odi_model_comparison.csv"
    )

    comparison.to_csv(
        comparison_file,
        index=False,
    )

    # ---------------------------------------------------------
    # Feature importance for best model
    # ---------------------------------------------------------

    importance = extract_feature_importance(
        best_model,
        FEATURE_COLUMNS,
    )

    importance_file = (
        MODEL_DIR
        / "odi_feature_importance.csv"
    )

    if not importance.empty:
        importance.to_csv(
            importance_file,
            index=False,
        )

    # ---------------------------------------------------------
    # Confusion matrices
    # ---------------------------------------------------------

    confusion_file = save_confusion_matrices(
        results,
        y_test,
    )

    # ---------------------------------------------------------
    # Metadata
    # ---------------------------------------------------------

    metadata = {
        "project": "Cricket Analytics",
        "model_type": "ODI binary winner prediction",
        "competition": "International ODI",
        "gender": "male",
        "dataset_rows": int(len(df)),
        "training_rows": int(len(train_df)),
        "testing_rows": int(len(test_df)),
        "train_ratio": TRAIN_RATIO,
        "random_state": RANDOM_STATE,
        "train_start": str(train_df["match_date"].min().date()),
        "train_end": str(train_df["match_date"].max().date()),
        "test_start": str(test_df["match_date"].min().date()),
        "test_end": str(test_df["match_date"].max().date()),
        "feature_count": len(FEATURE_COLUMNS),
        "features": FEATURE_COLUMNS,
        "best_model": best_name,
        "model_selection": (
            "Highest ROC-AUC, with lower Log Loss as tie-breaker"
        ),
        "models": comparison.to_dict(
            orient="records"
        ),
    }

    metadata_file = (
        MODEL_DIR
        / "odi_model_metadata.json"
    )

    with metadata_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            indent=2,
        )

    # ---------------------------------------------------------
    # Final report
    # ---------------------------------------------------------

    print()
    print("=" * 72)
    print("MODEL COMPARISON")
    print("=" * 72)

    display_columns = [
        "model",
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "log_loss",
        "brier_score",
    ]

    print(
        comparison[display_columns].to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    print()
    print("=" * 72)
    print(f"BEST MODEL: {best_name}")
    print("=" * 72)
    print()
    print(f"Saved best model:")
    print(best_model_file)
    print()
    print("Other outputs:")
    print(comparison_file)
    print(importance_file)
    print(confusion_file)
    print(metadata_file)
    print()

    # ---------------------------------------------------------
    # Top feature importance
    # ---------------------------------------------------------

    if not importance.empty:
        print("TOP 15 FEATURES")
        print("-" * 72)
        print(
            importance.head(15).to_string(
                index=False,
                float_format=lambda x: f"{x:.6f}",
            )
        )

    print()
    print("=" * 72)
    print("TRAINING COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
