import os
"""
ODI Match Predictor - Local Prediction Engine

Usage:
    python .\ml\scripts\predict_odi.py "India" "Australia" "Wankhede Stadium"

This is the first production-style prediction engine. It:
    1. Loads the frozen ODI V2 production model.
    2. Connects to the cricket_analytics MySQL database.
    3. Finds the requested men's ODI teams and venue.
    4. Reconstructs the 51 V2 features using only historical matches
       before the supplied prediction date.
    5. Produces Team A / Team B win probabilities.

Optional fourth argument:
    prediction date in YYYY-MM-DD format.

If omitted, today's local system date is used.

IMPORTANT:
    This engine intentionally performs a PRE-MATCH, PRE-TOSS prediction.
    Current/future match data is never used when constructing features.
"""

import sys
import warnings
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path

import joblib
import pandas as pd
import mysql.connector


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

MODEL_FILE = (
    BASE_DIR
    / "ml"
    / "models"
    / "odi_v2_production_model.joblib"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "cricket_analytics",
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
}


# ============================================================
# PREDICTION SETTINGS
# ============================================================

SUPPORTED_GENDER = "male"

SUPPORTED_COMPETITION_NAME = (
    "International ODI"
)

DEFAULT_PREDICTION_DATE = date.today()


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(value):

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


# ============================================================
# DATABASE
# ============================================================

def connect_database():

    try:

        return mysql.connector.connect(
            **DB_CONFIG
        )

    except mysql.connector.Error as exc:

        print(
            "ERROR: Could not connect to MySQL."
        )

        print(exc)

        sys.exit(1)


def load_historical_data(
    connection,
    prediction_date,
):

    # --------------------------------------------------------
    # Teams
    # --------------------------------------------------------

    team_query = """
        SELECT
            id,
            name,
            short_name,
            gender
        FROM teams
        WHERE LOWER(gender) = 'male'
    """

    teams = pd.read_sql(
        team_query,
        connection,
    )

    # --------------------------------------------------------
    # Competitions
    # --------------------------------------------------------

    competition_query = """
        SELECT
            id,
            name
        FROM competitions
        WHERE LOWER(name) = LOWER(%s)
    """

    competitions = pd.read_sql(
        competition_query,
        connection,
        params=(
            SUPPORTED_COMPETITION_NAME,
        ),
    )

    if competitions.empty:

        raise RuntimeError(
            "International ODI competition was not found."
        )

    competition_ids = tuple(
        int(value)
        for value in competitions["id"]
    )

    # --------------------------------------------------------
    # Matches
    # --------------------------------------------------------

    placeholders = ",".join(
        ["%s"] * len(competition_ids)
    )

    match_query = f"""
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
        WHERE m.competition_id IN ({placeholders})
          AND m.match_date < %s
          AND m.counted_in_standings = TRUE
        ORDER BY
            m.match_date,
            m.id
    """

    match_params = (
        *competition_ids,
        prediction_date,
    )

    matches = pd.read_sql(
        match_query,
        connection,
        params=match_params,
    )

    # --------------------------------------------------------
    # Match team statistics
    # --------------------------------------------------------

    stats_query = f"""
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
        WHERE m.competition_id IN ({placeholders})
          AND m.match_date < %s
          AND m.counted_in_standings = TRUE
        ORDER BY
            m.match_date,
            m.id,
            s.id
    """

    stats = pd.read_sql(
        stats_query,
        connection,
        params=match_params,
    )

    # --------------------------------------------------------
    # Venues
    # --------------------------------------------------------

    venue_query = """
        SELECT
            id,
            name,
            city,
            country
        FROM venues
    """

    venues = pd.read_sql(
        venue_query,
        connection,
    )

    return (
        teams,
        matches,
        stats,
        venues,
    )


# ============================================================
# ENTITY RESOLUTION
# ============================================================

def resolve_team(
    teams,
    requested_name,
):

    target = normalize_text(
        requested_name
    )

    exact_name = teams[
        teams["name"]
        .fillna("")
        .map(normalize_text)
        .eq(target)
    ]

    if len(exact_name) == 1:

        return exact_name.iloc[0]

    exact_short = teams[
        teams["short_name"]
        .fillna("")
        .map(normalize_text)
        .eq(target)
    ]

    if len(exact_short) == 1:

        return exact_short.iloc[0]

    candidates = teams[
        teams["name"]
        .fillna("")
        .map(normalize_text)
        .str.contains(
            target,
            regex=False,
        )
        |
        teams["short_name"]
        .fillna("")
        .map(normalize_text)
        .str.contains(
            target,
            regex=False,
        )
    ]

    if len(candidates) == 1:

        return candidates.iloc[0]

    if candidates.empty:

        raise ValueError(
            f"Team not found: {requested_name}"
        )

    names = [
        f"{row['name']} ({row['short_name']})"
        for _, row in candidates.iterrows()
    ]

    raise ValueError(
        "Team name is ambiguous. "
        f"Candidates: {', '.join(names)}"
    )


def resolve_venue(
    venues,
    requested_name,
):

    target = normalize_text(
        requested_name
    )

    exact = venues[
        venues["name"]
        .fillna("")
        .map(normalize_text)
        .eq(target)
    ]

    if len(exact) == 1:

        return exact.iloc[0]

    candidates = venues[
        venues["name"]
        .fillna("")
        .map(normalize_text)
        .str.contains(
            target,
            regex=False,
        )
    ]

    if len(candidates) == 1:

        return candidates.iloc[0]

    if candidates.empty:

        raise ValueError(
            f"Venue not found: {requested_name}"
        )

    names = [
        str(row["name"])
        for _, row in candidates.iterrows()
    ]

    raise ValueError(
        "Venue name is ambiguous. "
        f"Candidates: {', '.join(names[:20])}"
    )


# ============================================================
# HISTORICAL STATE
# ============================================================

def safe_rate(
    numerator,
    denominator,
):

    # Exact semantics used by the ODI V1 training builder:
    # no decided observations -> neutral 0.5.
    if denominator <= 0:
        return 0.5

    return numerator / denominator


def safe_ratio(
    numerator,
    denominator,
):

    # Exact semantics used by the ODI V2 builder:
    # zero denominator -> neutral ratio 1.0.
    if denominator == 0:
        return 1.0

    return numerator / denominator


def calculate_features(
    matches,
    stats,
    team_a_id,
    team_b_id,
    venue_id,
):
    """
    Reconstruct the V1/V2 features.

    Every value is based only on matches appearing before the
    requested prediction date because `matches` has already been
    filtered by match_date < prediction_date.

    Historical state is updated match-by-match.
    """

    # --------------------------------------------------------
    # Team state
    # --------------------------------------------------------

    team_state = defaultdict(
        lambda: {
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "decided": 0,
            "runs": 0,
            "wickets": 0,
            "performance_matches": 0,
            "recent_results": deque(
                maxlen=10
            ),
        }
    )

    # --------------------------------------------------------
    # Venue/team state
    # --------------------------------------------------------

    venue_state = defaultdict(
        lambda: {
            "matches": 0,
            "wins": 0,
            "losses": 0,
        }
    )

    # --------------------------------------------------------
    # H2H state
    # --------------------------------------------------------

    h2h = {
        "matches": 0,
        "a_wins": 0,
        "b_wins": 0,
    }

    # --------------------------------------------------------
    # Statistics lookup
    # --------------------------------------------------------

    stats_by_match_team = {}

    for _, row in stats.iterrows():

        key = (
            int(row["match_id"]),
            int(row["team_id"]),
        )

        stats_by_match_team[
            key
        ] = row

    # --------------------------------------------------------
    # Chronological replay
    # --------------------------------------------------------

    for _, match in matches.iterrows():

        match_id = int(
            match["id"]
        )

        team1 = int(
            match["team1_id"]
        )

        team2 = int(
            match["team2_id"]
        )

        venue = (
            int(match["venue_id"])
            if pd.notna(
                match["venue_id"]
            )
            else None
        )

        winner = (
            int(match["winner_team_id"])
            if pd.notna(
                match["winner_team_id"]
            )
            else None
        )

        status = normalize_text(
            match["match_status"]
        )

        # ----------------------------------------------------
        # Exact historical-state update used by the V1 builder.
        # ----------------------------------------------------

        participating = {team_a_id, team_b_id}

        for team_id in participating:

            state = team_state[
                team_id
            ]

            state["matches"] += 1

            stat = stats_by_match_team.get(
                (
                    match_id,
                    team_id,
                )
            )

            if stat is not None:

                state["runs"] += int(
                    stat["runs"]
                )

                state["wickets"] += int(
                    stat["wickets"]
                )

                state["performance_matches"] += 1

        # ----------------------------------------------------
        # Match result classification.
        #
        # The training builder classifies by winner_team_id.
        # Ties/no-results therefore remain neutral unless a valid
        # winner is actually recorded.
        # ----------------------------------------------------

        for team_id in participating:

            if winner == team_id:

                result = "W"

            elif winner in participating:

                result = "L"

            else:

                result = "NR"

            state = team_state[
                team_id
            ]

            if result == "W":

                state["wins"] += 1
                state["decided"] += 1

            elif result == "L":

                state["losses"] += 1
                state["decided"] += 1

            state["recent_results"].append(
                result
            )

                # ----------------------------------------------------
        # Venue history
        # ----------------------------------------------------

        if venue is not None:

            for team_id in participating:

                venue_key = (
                    team_id,
                    venue,
                )

                venue_state[
                    venue_key
                ]["matches"] += 1

                if winner == team_id:

                    venue_state[
                        venue_key
                    ]["wins"] += 1

                elif winner in participating:

                    venue_state[
                        venue_key
                    ]["losses"] += 1

        # ----------------------------------------------------
        # Head-to-head
        # ----------------------------------------------------

        if {
            team1,
            team2,
        } == {
            team_a_id,
            team_b_id,
        }:

            h2h[
                "matches"
            ] += 1

            if winner == team_a_id:

                h2h[
                    "a_wins"
                ] += 1

            elif winner == team_b_id:

                h2h[
                    "b_wins"
                ] += 1

    # ========================================================
    # EXTRACT TEAM A/B STATE
    # ========================================================

    a = team_state[
        int(team_a_id)
    ]

    b = team_state[
        int(team_b_id)
    ]

    # --------------------------------------------------------
    # Recent form
    # --------------------------------------------------------

    def recent_rate(
        results,
        window,
    ):

        values = list(
            results
        )[-window:]

        wins = sum(
            value == "W"
            for value in values
        )

        decided = sum(
            value in ("W", "L")
            for value in values
        )

        return safe_rate(
            wins,
            decided,
        )

    a_last5 = recent_rate(
        a["recent_results"],
        5,
    )

    b_last5 = recent_rate(
        b["recent_results"],
        5,
    )

    a_last10 = recent_rate(
        a["recent_results"],
        10,
    )

    b_last10 = recent_rate(
        b["recent_results"],
        10,
    )

    # --------------------------------------------------------
    # Venue
    # --------------------------------------------------------

    a_venue = venue_state[
        (
            int(team_a_id),
            int(venue_id),
        )
    ]

    b_venue = venue_state[
        (
            int(team_b_id),
            int(venue_id),
        )
    ]

    a_venue_rate = safe_rate(
        a_venue["wins"],
        a_venue["wins"]
        + a_venue["losses"],
    )

    b_venue_rate = safe_rate(
        b_venue["wins"],
        b_venue["wins"]
        + b_venue["losses"],
    )

    # --------------------------------------------------------
    # Core V1 features
    # --------------------------------------------------------

    a_win_rate = safe_rate(
        a["wins"],
        a["decided"],
    )

    b_win_rate = safe_rate(
        b["wins"],
        b["decided"],
    )

    a_avg_runs = (
        round(
            a["runs"]
            / a["performance_matches"],
            4,
        )
        if a["performance_matches"]
        else 0.0
    )

    b_avg_runs = (
        round(
            b["runs"]
            / b["performance_matches"],
            4,
        )
        if b["performance_matches"]
        else 0.0
    )

    a_avg_wickets = (
        round(
            a["wickets"]
            / a["performance_matches"],
            4,
        )
        if a["performance_matches"]
        else 0.0
    )

    b_avg_wickets = (
        round(
            b["wickets"]
            / b["performance_matches"],
            4,
        )
        if b["performance_matches"]
        else 0.0
    )

    # ========================================================
    # V1 FEATURE DICTIONARY
    # ========================================================

    features = {
        "team_a_matches_before":
            a["matches"],

        "team_b_matches_before":
            b["matches"],

        "team_a_wins_before":
            a["wins"],

        "team_b_wins_before":
            b["wins"],

        "team_a_decided_matches_before":
            a["decided"],

        "team_b_decided_matches_before":
            b["decided"],

        "team_a_win_rate":
            a_win_rate,

        "team_b_win_rate":
            b_win_rate,

        "team_a_last5_win_rate":
            a_last5,

        "team_b_last5_win_rate":
            b_last5,

        "team_a_last10_win_rate":
            a_last10,

        "team_b_last10_win_rate":
            b_last10,

        "team_a_avg_runs":
            a_avg_runs,

        "team_b_avg_runs":
            b_avg_runs,

        "team_a_avg_wickets":
            a_avg_wickets,

        "team_b_avg_wickets":
            b_avg_wickets,

        "team_a_venue_matches_before":
            a_venue["matches"],

        "team_b_venue_matches_before":
            b_venue["matches"],

        "team_a_venue_win_rate":
            a_venue_rate,

        "team_b_venue_win_rate":
            b_venue_rate,

        "head_to_head_matches_before":
            h2h["matches"],

        "head_to_head_a_wins":
            h2h["a_wins"],

        "head_to_head_b_wins":
            h2h["b_wins"],

        "head_to_head_a_win_rate":
            safe_rate(
                h2h["a_wins"],
                h2h["matches"],
            ),

        "head_to_head_b_win_rate":
            safe_rate(
                h2h["b_wins"],
                h2h["matches"],
            ),
    }

    # ========================================================
    # V2 ENGINEERED FEATURES
    # ========================================================

    features[
        "matches_before_difference"
    ] = (
        a["matches"]
        - b["matches"]
    )

    features[
        "wins_before_difference"
    ] = (
        a["wins"]
        - b["wins"]
    )

    features[
        "decided_matches_difference"
    ] = (
        a["decided"]
        - b["decided"]
    )

    features[
        "win_rate_difference"
    ] = (
        a_win_rate
        - b_win_rate
    )

    features[
        "last5_win_rate_difference"
    ] = (
        a_last5
        - b_last5
    )

    features[
        "last10_win_rate_difference"
    ] = (
        a_last10
        - b_last10
    )

    features[
        "avg_runs_difference"
    ] = (
        a_avg_runs
        - b_avg_runs
    )

    features[
        "avg_wickets_difference"
    ] = (
        a_avg_wickets
        - b_avg_wickets
    )

    features[
        "venue_matches_difference"
    ] = (
        a_venue["matches"]
        - b_venue["matches"]
    )

    features[
        "venue_win_rate_difference"
    ] = (
        a_venue_rate
        - b_venue_rate
    )

    features[
        "h2h_wins_difference"
    ] = (
        h2h["a_wins"]
        - h2h["b_wins"]
    )

    features[
        "h2h_win_rate_difference"
    ] = (
        safe_rate(
            h2h["a_wins"],
            h2h["matches"],
        )
        -
        safe_rate(
            h2h["b_wins"],
            h2h["matches"],
        )
    )

    features[
        "experience_ratio"
    ] = safe_ratio(
        a["matches"],
        b["matches"],
    )

    features[
        "win_count_ratio"
    ] = safe_ratio(
        a["wins"],
        b["wins"],
    )

    features[
        "avg_runs_ratio"
    ] = safe_ratio(
        a_avg_runs,
        b_avg_runs,
    )

    features[
        "avg_wickets_ratio"
    ] = safe_ratio(
        a_avg_wickets,
        b_avg_wickets,
    )

    features[
        "abs_win_rate_difference"
    ] = abs(
        a_win_rate
        - b_win_rate
    )

    features[
        "abs_last5_difference"
    ] = abs(
        a_last5
        - b_last5
    )

    features[
        "abs_last10_difference"
    ] = abs(
        a_last10
        - b_last10
    )

    features[
        "abs_avg_runs_difference"
    ] = abs(
        a_avg_runs
        - b_avg_runs
    )

    features[
        "abs_avg_wickets_difference"
    ] = abs(
        a_avg_wickets
        - b_avg_wickets
    )

    features[
        "team_a_win_rate_advantage"
    ] = int(
        a_win_rate > b_win_rate
    )

    features[
        "team_a_recent5_advantage"
    ] = int(
        a_last5 > b_last5
    )

    features[
        "team_a_recent10_advantage"
    ] = int(
        a_last10 > b_last10
    )

    features[
        "team_a_venue_advantage"
    ] = int(
        a_venue_rate > b_venue_rate
    )

    features[
        "team_a_h2h_advantage"
    ] = int(
        safe_rate(
            h2h["a_wins"],
            h2h["a_wins"]
            + h2h["b_wins"],
        )
        >
        safe_rate(
            h2h["b_wins"],
            h2h["a_wins"]
            + h2h["b_wins"],
        )
    )

    return features


# ============================================================
# PREDICTION
# ============================================================

def predict(
    model_package,
    features,
):

    feature_columns = (
        model_package[
            "feature_columns"
        ]
    )

    missing = [
        column
        for column in feature_columns
        if column not in features
    ]

    if missing:

        raise RuntimeError(
            "Missing model features: "
            + ", ".join(missing)
        )

    vector = pd.DataFrame(
        [
            [
                features[column]
                for column in feature_columns
            ]
        ],
        columns=feature_columns,
    )

    model = model_package[
        "model"
    ]

    probability_a = float(
        model
        .predict_proba(
            vector
        )[0, 1]
    )

    probability_b = (
        1.0
        - probability_a
    )

    prediction = (
        "Team A"
        if probability_a >= 0.50
        else "Team B"
    )

    return (
        probability_a,
        probability_b,
        prediction,
        vector,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if len(sys.argv) < 4:

        print(
            "Usage:"
        )

        print(
            'python .\\ml\\scripts\\predict_odi.py '
            '"India" "Australia" "Wankhede Stadium" '
            '[YYYY-MM-DD]'
        )

        sys.exit(1)

    team_a_name = sys.argv[1]

    team_b_name = sys.argv[2]

    venue_name = sys.argv[3]

    if len(sys.argv) >= 5:

        try:

            prediction_date = datetime.strptime(
                sys.argv[4],
                "%Y-%m-%d",
            ).date()

        except ValueError:

            print(
                "ERROR: Prediction date must be "
                "YYYY-MM-DD."
            )

            sys.exit(1)

    else:

        prediction_date = (
            DEFAULT_PREDICTION_DATE
        )

    if team_a_name.strip().lower() == team_b_name.strip().lower():

        print(
            "ERROR: Team A and Team B must be different."
        )

        sys.exit(1)

    # ========================================================
    # MODEL
    # ========================================================

    if not MODEL_FILE.exists():

        print(
            "ERROR: Production model not found:"
        )

        print(MODEL_FILE)

        sys.exit(1)

    package = joblib.load(
        MODEL_FILE
    )

    if (
        package.get(
            "feature_set"
        )
        != "V2"
    ):

        print(
            "ERROR: Unexpected feature set."
        )

        sys.exit(1)

    if (
        package.get(
            "feature_count"
        )
        != 51
    ):

        print(
            "ERROR: Expected 51 features."
        )

        sys.exit(1)

    # ========================================================
    # DATABASE
    # ========================================================

    connection = connect_database()

    try:

        (
            teams,
            matches,
            stats,
            venues,
        ) = load_historical_data(
            connection,
            prediction_date,
        )

    finally:

        connection.close()

    # ========================================================
    # RESOLVE ENTITIES
    # ========================================================

    team_a = resolve_team(
        teams,
        team_a_name,
    )

    team_b = resolve_team(
        teams,
        team_b_name,
    )

    venue = resolve_venue(
        venues,
        venue_name,
    )

    team_a_id = int(
        team_a["id"]
    )

    team_b_id = int(
        team_b["id"]
    )

    venue_id = int(
        venue["id"]
    )

    # ========================================================
    # FILTER HISTORICAL MATCHES TO RELEVANT TEAM/COMPETITION
    # ========================================================

    relevant_matches = matches[
        (
            (
                matches["team1_id"]
                == team_a_id
            )
            |
            (
                matches["team2_id"]
                == team_a_id
            )
            |
            (
                matches["team1_id"]
                == team_b_id
            )
            |
            (
                matches["team2_id"]
                == team_b_id
            )
        )
    ].copy()

    # We need all historical matches for these teams to
    # calculate their individual histories, plus matches between
    # the two teams for H2H.
    relevant_match_ids = set(
        int(value)
        for value in relevant_matches["id"]
    )

    relevant_stats = stats[
        stats["match_id"].isin(
            relevant_match_ids
        )
    ].copy()

    # ========================================================
    # FEATURES
    # ========================================================

    features = calculate_features(
        relevant_matches,
        relevant_stats,
        team_a_id,
        team_b_id,
        venue_id,
    )

    # ========================================================
    # PREDICT
    # ========================================================

    (
        probability_a,
        probability_b,
        prediction,
        vector,
    ) = predict(
        package,
        features,
    )

    predicted_name = (
        team_a["name"]
        if prediction == "Team A"
        else team_b["name"]
    )

    # ========================================================
    # DISPLAY
    # ========================================================

    print("=" * 72)
    print(
        "ODI MATCH PREDICTION"
    )
    print("=" * 72)
    print()

    print(
        f"Team A : {team_a['name']}"
    )

    print(
        f"Team B : {team_b['name']}"
    )

    print(
        f"Venue  : {venue['name']}"
    )

    print(
        f"Date   : {prediction_date}"
    )

    print()

    print(
        "MODEL"
    )

    print(
        "-" * 72
    )

    print(
        f"Model       : "
        f"{package['model_type']}"
    )

    print(
        f"Feature set : "
        f"{package['feature_set']}"
    )

    print(
        f"Features    : "
        f"{package['feature_count']}"
    )

    print(
        f"C           : "
        f"{package['regularization_C']}"
    )

    print(
        "Prediction  : "
        "Pre-match / Pre-toss"
    )

    print()

    print(
        "HISTORICAL SAMPLE"
    )

    print(
        "-" * 72
    )

    print(
        f"Team A matches before : "
        f"{features['team_a_matches_before']}"
    )

    print(
        f"Team B matches before : "
        f"{features['team_b_matches_before']}"
    )

    print(
        f"H2H matches before    : "
        f"{features['head_to_head_matches_before']}"
    )

    print(
        f"Team A venue matches  : "
        f"{features['team_a_venue_matches_before']}"
    )

    print(
        f"Team B venue matches  : "
        f"{features['team_b_venue_matches_before']}"
    )

    print()

    print(
        "PREDICTION"
    )

    print(
        "-" * 72
    )

    print(
        f"{team_a['name']:<30}"
        f"{probability_a * 100:6.2f}%"
    )

    print(
        f"{team_b['name']:<30}"
        f"{probability_b * 100:6.2f}%"
    )

    print()

    print(
        f"Predicted winner : "
        f"{predicted_name}"
    )

    print()

    print(
        "51-FEATURE VECTOR"
    )

    print(
        "-" * 72
    )

    for column in package[
        "feature_columns"
    ]:

        print(
            f"{column:<42}"
            f"{features[column]}"
        )

    print()
    print(
        "Prediction engine completed successfully."
    )

    print()
    print(
        "NOTE: Feature reconstruction now follows the "
        "training-builder semantics for V1/V2 rates, "
        "averages, recent form, venue rates, H2H rates, "
        "and ratios."
    )


if __name__ == "__main__":
    main()

