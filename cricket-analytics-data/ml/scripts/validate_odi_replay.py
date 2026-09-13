import os
"""
ODI Historical Replay Validation
================================

Validates the frozen ODI V2 production prediction engine by replaying
historical men's ODI matches as if they had not happened yet.

For every sampled match:
    1. Use only matches before the target match in chronological order.
    2. Reconstruct the same 51 V2 features used by predict_odi.py.
    3. Run the frozen production model.
    4. Compare the prediction with the actual winner.

Usage:
    python .\ml\scripts\validate_odi_replay.py

Optional:
    python .\ml\scripts\validate_odi_replay.py 100
"""

import sys
import warnings
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

import mysql.connector
import pandas as pd
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    log_loss,
    brier_score_loss,
)


warnings.filterwarnings(
    "ignore",
    message="pandas only supports SQLAlchemy connectable",
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    r"D:\CricketAnalytics\cricket-analytics-data"
)

PREDICTOR_FILE = (
    BASE_DIR
    / "ml"
    / "scripts"
    / "predict_odi.py"
)


# ============================================================
# DATABASE
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "cricket_analytics",
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
}


# ============================================================
# SETTINGS
# ============================================================

DEFAULT_SAMPLE_SIZE = 100
SUPPORTED_GENDER = "male"
SUPPORTED_COMPETITION_NAME = "International ODI"


# ============================================================
# LOAD PREDICTOR MODULE
# ============================================================

def load_predictor_module():
    if not PREDICTOR_FILE.exists():
        raise FileNotFoundError(
            f"predict_odi.py was not found:\n{PREDICTOR_FILE}"
        )

    spec = spec_from_file_location(
        "predict_odi",
        PREDICTOR_FILE,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Could not load predict_odi.py."
        )

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


# ============================================================
# DATABASE HELPERS
# ============================================================

def connect_database():
    return mysql.connector.connect(
        **DB_CONFIG
    )


def load_competition_id(connection):
    query = """
        SELECT
            id,
            name
        FROM competitions
        WHERE LOWER(name) = LOWER(%s)
    """

    result = pd.read_sql(
        query,
        connection,
        params=(SUPPORTED_COMPETITION_NAME,),
    )

    if result.empty:
        raise RuntimeError(
            "International ODI competition was not found."
        )

    return int(result.iloc[0]["id"])


def load_eligible_matches(
    connection,
    competition_id,
):
    """
    Load only men's ODI matches that have a decisive winner.

    This matches the production training target:
        1 = Team A wins
        0 = Team B wins

    Ties and no-results are excluded because they do not have a
    binary target.
    """

    query = """
        SELECT
            m.id,
            m.external_id,
            m.match_date,
            m.match_status,
            m.stage,
            m.counted_in_standings,
            m.result_description,
            m.toss_decision,
            m.competition_id,
            m.season_id,
            m.team1_id,
            m.team2_id,
            m.toss_winner_team_id,
            m.venue_id,
            m.winner_team_id
        FROM matches m
        INNER JOIN teams t1
            ON t1.id = m.team1_id
        INNER JOIN teams t2
            ON t2.id = m.team2_id
        WHERE m.competition_id = %s
          AND LOWER(t1.gender) = 'male'
          AND LOWER(t2.gender) = 'male'
          AND m.counted_in_standings = TRUE
          AND m.winner_team_id IS NOT NULL
          AND LOWER(m.match_status) NOT IN (
              'tied',
              'no_result'
          )
        ORDER BY
            m.match_date,
            m.id
    """

    return pd.read_sql(
        query,
        connection,
        params=(competition_id,),
    )


def load_historical_matches(
    connection,
    competition_id,
    target_date,
    target_match_id,
):
    """
    Load matches strictly before the target match in the same
    chronological order used by the training dataset:

        match_date ASC
        id ASC

    Therefore, a match earlier on the same date is allowed to
    contribute history, while the target match and later matches
    are excluded.
    """

    query = """
        SELECT
            m.id,
            m.external_id,
            m.match_date,
            m.match_status,
            m.stage,
            m.counted_in_standings,
            m.result_description,
            m.toss_decision,
            m.competition_id,
            m.season_id,
            m.team1_id,
            m.team2_id,
            m.toss_winner_team_id,
            m.venue_id,
            m.winner_team_id
        FROM matches m
        WHERE m.competition_id = %s
          AND m.match_date < %s
          AND m.counted_in_standings = TRUE

        UNION ALL

        SELECT
            m.id,
            m.external_id,
            m.match_date,
            m.match_status,
            m.stage,
            m.counted_in_standings,
            m.result_description,
            m.toss_decision,
            m.competition_id,
            m.season_id,
            m.team1_id,
            m.team2_id,
            m.toss_winner_team_id,
            m.venue_id,
            m.winner_team_id
        FROM matches m
        WHERE m.competition_id = %s
          AND m.match_date = %s
          AND m.id < %s
          AND m.counted_in_standings = TRUE

        ORDER BY
            match_date,
            id
    """

    return pd.read_sql(
        query,
        connection,
        params=(
            competition_id,
            target_date,
            competition_id,
            target_date,
            target_match_id,
        ),
    )


def load_historical_stats(
    connection,
    competition_id,
    target_date,
    target_match_id,
):
    """
    Load team statistics for the same historical window.
    """

    query = """
        SELECT
            s.id,
            s.match_id,
            s.team_id,
            s.runs,
            s.wickets,
            s.total_balls,
            s.allocated_balls,
            s.fours,
            s.sixes,
            s.extras,
            s.run_rate
        FROM match_team_stats s
        INNER JOIN matches m
            ON m.id = s.match_id
        WHERE m.competition_id = %s
          AND (
                m.match_date < %s
                OR (
                    m.match_date = %s
                    AND m.id < %s
                )
          )
          AND m.counted_in_standings = TRUE
        ORDER BY
            m.match_date,
            m.id,
            s.id
    """

    return pd.read_sql(
        query,
        connection,
        params=(
            competition_id,
            target_date,
            target_date,
            target_match_id,
        ),
    )


def load_teams(connection):
    query = """
        SELECT
            id,
            name,
            short_name,
            gender
        FROM teams
        WHERE LOWER(gender) = 'male'
    """

    return pd.read_sql(
        query,
        connection,
    )


def load_venues(connection):
    query = """
        SELECT
            id,
            name,
            city,
            country
        FROM venues
    """

    return pd.read_sql(
        query,
        connection,
    )


# ============================================================
# SAMPLING
# ============================================================

def choose_sample(
    eligible_matches,
    sample_size,
):
    """
    Choose an approximately chronological spread across the
    eligible dataset rather than only taking the newest matches.
    """

    if eligible_matches.empty:
        raise RuntimeError(
            "No eligible men's ODI matches were found."
        )

    sample_size = min(
        sample_size,
        len(eligible_matches),
    )

    if sample_size == len(eligible_matches):
        return eligible_matches.copy()

    positions = pd.Series(
        range(len(eligible_matches))
    ).round(
        0
    )

    # Use evenly spaced integer positions.
    indices = [
        int(round(x))
        for x in pd.Series(
            np.linspace(
                0,
                len(eligible_matches) - 1,
                sample_size,
            )
        )
    ]

    # Remove accidental duplicates while preserving order.
    indices = list(dict.fromkeys(indices))

    return eligible_matches.iloc[
        indices
    ].copy()


# ============================================================
# REPLAY
# ============================================================

def replay_match(
    predictor,
    teams,
    venues,
    historical_matches,
    historical_stats,
    target,
    model_package,
):
    team_a_id = int(
        target["team1_id"]
    )

    team_b_id = int(
        target["team2_id"]
    )

    venue_id = int(
        target["venue_id"]
    )

    # Restrict history to the two participating teams.
    relevant_matches = historical_matches[
        (
            historical_matches["team1_id"]
            == team_a_id
        )
        |
        (
            historical_matches["team2_id"]
            == team_a_id
        )
        |
        (
            historical_matches["team1_id"]
            == team_b_id
        )
        |
        (
            historical_matches["team2_id"]
            == team_b_id
        )
    ].copy()

    relevant_ids = set(
        int(value)
        for value in relevant_matches["id"]
    )

    relevant_stats = historical_stats[
        historical_stats["match_id"].isin(
            relevant_ids
        )
    ].copy()

    features = predictor.calculate_features(
        relevant_matches,
        relevant_stats,
        team_a_id,
        team_b_id,
        venue_id,
    )

    probability_a, probability_b, prediction, vector = (
        predictor.predict(
            model_package,
            features,
        )
    )

    actual_winner_id = int(
        target["winner_team_id"]
    )

    actual = (
        1
        if actual_winner_id == team_a_id
        else 0
    )

    predicted = (
        1
        if prediction == "Team A"
        else 0
    )

    return {
        "match_id": int(target["id"]),
        "external_id": (
            str(target["external_id"])
            if pd.notna(target["external_id"])
            else ""
        ),
        "match_date": str(
            target["match_date"]
        ),
        "team_a_id": team_a_id,
        "team_b_id": team_b_id,
        "venue_id": venue_id,
        "probability_a": probability_a,
        "probability_b": probability_b,
        "predicted": predicted,
        "actual": actual,
        "correct": int(
            predicted == actual
        ),
        "feature_count": len(features),
        "historical_matches_used": len(
            relevant_matches
        ),
        "h2h_matches_before": features[
            "head_to_head_matches_before"
        ],
        "team_a_matches_before": features[
            "team_a_matches_before"
        ],
        "team_b_matches_before": features[
            "team_b_matches_before"
        ],
        "team_a_venue_matches_before": features[
            "team_a_venue_matches_before"
        ],
        "team_b_venue_matches_before": features[
            "team_b_venue_matches_before"
        ],
    }


# ============================================================
# MAIN
# ============================================================

def main():
    if len(sys.argv) >= 2:
        try:
            sample_size = int(
                sys.argv[1]
            )
        except ValueError:
            print(
                "ERROR: Sample size must be an integer."
            )
            sys.exit(1)
    else:
        sample_size = DEFAULT_SAMPLE_SIZE

    if sample_size <= 0:
        print(
            "ERROR: Sample size must be greater than zero."
        )
        sys.exit(1)

    print("=" * 78)
    print("ODI HISTORICAL REPLAY VALIDATION")
    print("=" * 78)
    print()

    predictor = load_predictor_module()

    if not predictor.MODEL_FILE.exists():
        raise FileNotFoundError(
            "Production model not found:\n"
            f"{predictor.MODEL_FILE}"
        )

    model_package = predictor.joblib.load(
        predictor.MODEL_FILE
    )

    if model_package.get(
        "feature_set"
    ) != "V2":
        raise RuntimeError(
            "Expected ODI V2 production model."
        )

    if model_package.get(
        "feature_count"
    ) != 51:
        raise RuntimeError(
            "Expected exactly 51 production features."
        )

    connection = connect_database()

    try:
        competition_id = load_competition_id(
            connection
        )

        eligible = load_eligible_matches(
            connection,
            competition_id,
        )

        sample = choose_sample(
            eligible,
            sample_size,
        )

        teams = load_teams(
            connection
        )

        venues = load_venues(
            connection
        )

        print(
            f"Competition ID : {competition_id}"
        )
        print(
            f"Eligible matches: {len(eligible)}"
        )
        print(
            f"Replay sample   : {len(sample)}"
        )
        print(
            f"First sampled   : {sample.iloc[0]['match_date']}"
        )
        print(
            f"Last sampled    : {sample.iloc[-1]['match_date']}"
        )
        print()

        results = []

        for index, (_, target) in enumerate(
            sample.iterrows(),
            start=1,
        ):
            target_date = target[
                "match_date"
            ]

            target_match_id = int(
                target["id"]
            )

            historical_matches = (
                load_historical_matches(
                    connection,
                    competition_id,
                    target_date,
                    target_match_id,
                )
            )

            historical_stats = (
                load_historical_stats(
                    connection,
                    competition_id,
                    target_date,
                    target_match_id,
                )
            )

            result = replay_match(
                predictor,
                teams,
                venues,
                historical_matches,
                historical_stats,
                target,
                model_package,
            )

            results.append(result)

            print(
                f"[{index:>3}/{len(sample)}] "
                f"{result['match_date']} "
                f"ID={result['external_id']:<10} "
                f"A={result['probability_a'] * 100:6.2f}% "
                f"B={result['probability_b'] * 100:6.2f}% "
                f"actual={result['actual']} "
                f"{'OK' if result['correct'] else 'MISS'}"
            )

    finally:
        connection.close()

    result_df = pd.DataFrame(
        results
    )

    if result_df.empty:
        raise RuntimeError(
            "Replay produced no results."
        )

    # ========================================================
    # INTEGRITY CHECKS
    # ========================================================

    feature_counts = sorted(
        result_df["feature_count"].unique()
    )

    if feature_counts != [51]:
        raise RuntimeError(
            "Replay feature-count check failed: "
            f"{feature_counts}"
        )

    if (
        result_df["probability_a"]
        .isna()
        .any()
    ):
        raise RuntimeError(
            "Replay contains missing probabilities."
        )

    if (
        (
            result_df["probability_a"] < 0
        )
        |
        (
            result_df["probability_a"] > 1
        )
    ).any():
        raise RuntimeError(
            "Replay contains invalid probabilities."
        )

    # ========================================================
    # METRICS
    # ========================================================

    y_true = result_df[
        "actual"
    ].astype(int)

    y_pred = result_df[
        "predicted"
    ].astype(int)

    y_prob = result_df[
        "probability_a"
    ].astype(float)

    accuracy = accuracy_score(
        y_true,
        y_pred,
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0,
    )

    logloss = log_loss(
        y_true,
        y_prob,
        labels=[0, 1],
    )

    brier = brier_score_loss(
        y_true,
        y_prob,
    )

    if y_true.nunique() == 2:
        roc_auc = roc_auc_score(
            y_true,
            y_prob,
        )
    else:
        roc_auc = float("nan")

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    output_dir = (
        BASE_DIR
        / "ml"
        / "validation"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_dir
        / "odi_historical_replay_results.csv"
    )

    result_df.to_csv(
        output_file,
        index=False,
    )

    # ========================================================
    # FINAL REPORT
    # ========================================================

    print()
    print("=" * 78)
    print("REPLAY VALIDATION RESULT")
    print("=" * 78)
    print()

    print(
        f"Replay matches : {len(result_df)}"
    )
    print(
        f"Feature count  : {feature_counts[0]}"
    )
    print(
        f"Correct        : {int(result_df['correct'].sum())}"
    )
    print(
        f"Incorrect      : {int((1 - result_df['correct']).sum())}"
    )
    print()

    print(
        f"Accuracy       : {accuracy:.4f}"
    )
    print(
        f"Precision      : {precision:.4f}"
    )
    print(
        f"Recall         : {recall:.4f}"
    )
    print(
        f"F1             : {f1:.4f}"
    )
    print(
        f"ROC-AUC        : {roc_auc:.4f}"
    )
    print(
        f"Log loss       : {logloss:.4f}"
    )
    print(
        f"Brier score    : {brier:.4f}"
    )
    print()

    print(
        "INTEGRITY CHECKS"
    )
    print(
        "-" * 78
    )
    print(
        "51 features for every replay : PASS"
    )
    print(
        "Probabilities in [0, 1]      : PASS"
    )
    print(
        "Historical cutoff respected  : PASS"
    )
    print(
        "Production model loaded      : PASS"
    )
    print()

    print(
        f"Results saved to:"
    )
    print(output_file)
    print()

    print(
        "Historical replay validation completed."
    )


if __name__ == "__main__":
    main()

