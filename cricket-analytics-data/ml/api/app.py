import os
from pathlib import Path
from datetime import date
from typing import Optional
import importlib.util

import joblib
import pandas as pd
import mysql.connector

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_FILE = (
    BASE_DIR
    / "ml"
    / "models"
    / "odi_v2_production_model.joblib"
)

PREDICTOR_FILE = (
    BASE_DIR
    / "ml"
    / "scripts"
    / "predict_odi.py"
)


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "database": os.getenv("DB_NAME", "cricket_analytics"),
    "user": os.getenv("DB_USERNAME", "root"),
    "password": os.getenv("DB_PASSWORD"),
}


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Cricket Analytics ML API",
    description=(
        "Machine-learning prediction API for "
        "Cricket Analytics."
    ),
    version="1.0.0",
)


# ============================================================
# REQUEST MODEL
# ============================================================

class ODIPredictionRequest(BaseModel):

    teamA: str = Field(
        ...,
        min_length=1,
        description="Team A name",
    )

    teamB: str = Field(
        ...,
        min_length=1,
        description="Team B name",
    )

    venue: str = Field(
        ...,
        min_length=1,
        description="Venue name",
    )

    predictionDate: Optional[date] = Field(
        default=None,
        description=(
            "Historical cutoff date. "
            "If omitted, today's date is used."
        ),
    )


# ============================================================
# RESPONSE MODEL
# ============================================================

class ODIPredictionResponse(BaseModel):

    teamA: str
    teamB: str
    venue: str
    predictionDate: str

    teamAWinProbability: float
    teamBWinProbability: float

    predictedWinner: str

    modelVersion: str
    modelType: str
    featureSet: str
    featureCount: int

    teamAMatchesBefore: int
    teamBMatchesBefore: int

    headToHeadMatchesBefore: int

    teamAVenueMatchesBefore: int
    teamBVenueMatchesBefore: int


# ============================================================
# GLOBAL ML RESOURCES
# ============================================================

predictor = None
model_package = None


# ============================================================
# LOAD predict_odi.py
# ============================================================

def load_predictor_module():

    if not PREDICTOR_FILE.exists():

        raise RuntimeError(
            "predict_odi.py was not found at:\n"
            f"{PREDICTOR_FILE}"
        )

    spec = importlib.util.spec_from_file_location(
        "predict_odi",
        PREDICTOR_FILE,
    )

    if spec is None or spec.loader is None:

        raise RuntimeError(
            "Could not create import specification "
            "for predict_odi.py."
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(module)

    return module


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def load_ml_resources():

    global predictor
    global model_package

    print()
    print("=" * 70)
    print("CRICKET ANALYTICS ML API")
    print("=" * 70)

    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    print(
        "Loading production model:"
    )

    print(
        MODEL_FILE
    )

    if not MODEL_FILE.exists():

        raise RuntimeError(
            "Production model does not exist:\n"
            f"{MODEL_FILE}"
        )

    # --------------------------------------------------------
    # Load predictor
    # --------------------------------------------------------

    predictor = load_predictor_module()

    print(
        "Prediction engine loaded successfully."
    )

    # --------------------------------------------------------
    # Load model artifact
    # --------------------------------------------------------

    model_package = joblib.load(
        MODEL_FILE
    )

    # --------------------------------------------------------
    # Validate artifact
    # --------------------------------------------------------

    if not isinstance(
        model_package,
        dict,
    ):

        raise RuntimeError(
            "Production model artifact must be "
            "a dictionary."
        )

    if model_package.get(
        "feature_set"
    ) != "V2":

        raise RuntimeError(
            "Expected V2 production model."
        )

    if model_package.get(
        "feature_count"
    ) != 51:

        raise RuntimeError(
            "Expected exactly 51 model features."
        )

    if "model" not in model_package:

        raise RuntimeError(
            "The production artifact does not "
            "contain the trained model."
        )

    if "feature_columns" not in model_package:

        raise RuntimeError(
            "The production artifact does not "
            "contain feature_columns."
        )

    if len(
        model_package["feature_columns"]
    ) != 51:

        raise RuntimeError(
            "Production artifact does not "
            "contain exactly 51 feature columns."
        )

    # --------------------------------------------------------
    # Print model information
    # --------------------------------------------------------

    print()
    print(
        "Model type    :",
        model_package.get(
            "model_type"
        ),
    )

    print(
        "Feature set   :",
        model_package.get(
            "feature_set"
        ),
    )

    print(
        "Feature count :",
        model_package.get(
            "feature_count"
        ),
    )

    print(
        "C             :",
        model_package.get(
            "regularization_C"
        ),
    )

    print(
        "Preprocessing :",
        model_package.get(
            "preprocessing"
        ),
    )

    print(
        "Model version :",
        model_package.get(
            "artifact_version"
        ),
    )

    print()
    print(
        "ML resources loaded successfully."
    )

    print("=" * 70)
    print()


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    try:

        return mysql.connector.connect(
            **DB_CONFIG
        )

    except mysql.connector.Error as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not connect to MySQL: "
                f"{exc}"
            ),
        )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    model_loaded = (
        model_package is not None
    )

    return {
        "status": "UP",
        "service": "Cricket Analytics ML API",
        "modelLoaded": model_loaded,
        "modelVersion": (
            model_package.get(
                "artifact_version"
            )
            if model_loaded
            else None
        ),
    }


# ============================================================
# MODEL INFORMATION
# ============================================================

@app.get("/model-info")
def model_info():

    if model_package is None:

        raise HTTPException(
            status_code=503,
            detail="ML model is not loaded.",
        )

    target = model_package.get(
        "target",
        {},
    )

    return {

        "version": model_package.get(
            "artifact_version"
        ),

        "modelType": model_package.get(
            "model_type"
        ),

        "featureSet": model_package.get(
            "feature_set"
        ),

        "featureCount": model_package.get(
            "feature_count"
        ),

        "C": model_package.get(
            "regularization_C"
        ),

        "preprocessing": model_package.get(
            "preprocessing"
        ),

        "target": target,

        "probabilityOutput": target.get(
            "probability"
        ),

        "calibration": model_package.get(
            "calibration"
        ),
    }


# ============================================================
# ODI PREDICTION
# ============================================================

@app.post(
    "/predict/odi",
    response_model=ODIPredictionResponse,
)
def predict_odi(
    request: ODIPredictionRequest,
):

    # ========================================================
    # Validate ML resources
    # ========================================================

    if predictor is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Prediction engine is not loaded."
            ),
        )

    if model_package is None:

        raise HTTPException(
            status_code=503,
            detail=(
                "Production model is not loaded."
            ),
        )

    # ========================================================
    # Clean request values
    # ========================================================

    team_a_name = request.teamA.strip()
    team_b_name = request.teamB.strip()
    venue_name = request.venue.strip()

    # ========================================================
    # Validate teams
    # ========================================================

    if (
        team_a_name.lower()
        == team_b_name.lower()
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Team A and Team B must be different."
            ),
        )

    # ========================================================
    # Prediction cutoff date
    # ========================================================

    prediction_date = (
        request.predictionDate
        if request.predictionDate is not None
        else date.today()
    )

    # ========================================================
    # Database connection
    # ========================================================

    connection = get_connection()

    try:

        # ====================================================
        # 1. FIND INTERNATIONAL ODI COMPETITION
        # ====================================================

        competition_query = """
            SELECT
                id,
                name
            FROM competitions
            WHERE LOWER(name)
                  = LOWER(%s)
        """

        competitions = pd.read_sql(
            competition_query,
            connection,
            params=(
                "International ODI",
            ),
        )

        if competitions.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    "International ODI competition "
                    "was not found."
                ),
            )

        competition_id = int(
            competitions.iloc[0]["id"]
        )

        # ====================================================
        # 2. FIND TEAM A
        # ====================================================

        team_query = """
            SELECT
                id,
                name,
                short_name,
                gender
            FROM teams
            WHERE LOWER(name)
                  = LOWER(%s)
              AND LOWER(gender)
                  = 'male'
        """

        team_a_df = pd.read_sql(
            team_query,
            connection,
            params=(
                team_a_name,
            ),
        )

        if team_a_df.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Men's ODI team not found: "
                    f"{team_a_name}"
                ),
            )

        team_a_id = int(
            team_a_df.iloc[0]["id"]
        )

        # ====================================================
        # 3. FIND TEAM B
        # ====================================================

        team_b_df = pd.read_sql(
            team_query,
            connection,
            params=(
                team_b_name,
            ),
        )

        if team_b_df.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Men's ODI team not found: "
                    f"{team_b_name}"
                ),
            )

        team_b_id = int(
            team_b_df.iloc[0]["id"]
        )

        # ====================================================
        # 4. FIND VENUE
        # ====================================================

        venue_query = """
            SELECT
                id,
                name,
                city,
                country
            FROM venues
            WHERE LOWER(name)
                  = LOWER(%s)
        """

        venue_df = pd.read_sql(
            venue_query,
            connection,
            params=(
                venue_name,
            ),
        )

        if venue_df.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Venue not found: "
                    f"{venue_name}"
                ),
            )

        venue_id = int(
            venue_df.iloc[0]["id"]
        )

        # ====================================================
        # 5. LOAD ALL HISTORICAL MEN'S ODI MATCHES
        #    BEFORE PREDICTION DATE
        # ====================================================

        matches_query = """
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
            ORDER BY
                m.match_date,
                m.id
        """

        historical_matches = pd.read_sql(
            matches_query,
            connection,
            params=(
                competition_id,
                prediction_date,
            ),
        )

        # ====================================================
        # 6. FILTER TO MATCHES INVOLVING EITHER TEAM
        # ====================================================

        relevant_matches = (
            historical_matches[
                (
                    historical_matches[
                        "team1_id"
                    ]
                    == team_a_id
                )
                |
                (
                    historical_matches[
                        "team2_id"
                    ]
                    == team_a_id
                )
                |
                (
                    historical_matches[
                        "team1_id"
                    ]
                    == team_b_id
                )
                |
                (
                    historical_matches[
                        "team2_id"
                    ]
                    == team_b_id
                )
            ]
        ).copy()

        relevant_ids = set(
            int(value)
            for value in relevant_matches[
                "id"
            ]
        )

        # ====================================================
        # 7. LOAD TEAM MATCH STATISTICS
        # ====================================================

        if relevant_ids:

            placeholders = ",".join(
                ["%s"] * len(relevant_ids)
            )

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
                WHERE s.match_id IN (
                    {placeholders}
                )
                ORDER BY
                    s.match_id,
                    s.id
            """

            relevant_stats = pd.read_sql(
                stats_query,
                connection,
                params=tuple(
                    relevant_ids
                ),
            )

        else:

            relevant_stats = pd.DataFrame(
                columns=[
                    "id",
                    "match_id",
                    "team_id",
                    "runs",
                    "wickets",
                    "total_balls",
                    "allocated_balls",
                    "fours",
                    "sixes",
                    "extras",
                    "run_rate",
                ]
            )

        # ====================================================
        # 8. RECONSTRUCT EXACT V2 FEATURES
        #
        #    This uses the feature reconstruction logic
        #    already implemented and validated in
        #    predict_odi.py.
        # ====================================================

        features = predictor.calculate_features(
            relevant_matches,
            relevant_stats,
            team_a_id,
            team_b_id,
            venue_id,
        )

        # ====================================================
        # 9. BUILD 51-FEATURE DATAFRAME
        # ====================================================

        feature_columns = model_package[
            "feature_columns"
        ]

        feature_vector = pd.DataFrame(
            [
                [
                    features[column]
                    for column in feature_columns
                ]
            ],
            columns=feature_columns,
        )

        # ====================================================
        # 10. RUN FROZEN PRODUCTION MODEL
        # ====================================================

        model = model_package[
            "model"
        ]

        probabilities = model.predict_proba(
            feature_vector
        )[0]

        # sklearn class ordering for our binary model:
        #
        # class 0 = Team B wins
        # class 1 = Team A wins
        #
        # Therefore:
        #
        # probabilities[0] = Team B
        # probabilities[1] = Team A

        probability_b = float(
            probabilities[0]
        )

        probability_a = float(
            probabilities[1]
        )

        # ====================================================
        # 11. DETERMINE WINNER
        # ====================================================

        prediction = (
            "Team A"
            if probability_a >= probability_b
            else "Team B"
        )

        predicted_winner = (
            team_a_name
            if prediction == "Team A"
            else team_b_name
        )

        # ====================================================
        # 12. RETURN API RESPONSE
        # ====================================================

        return {

            "teamA": team_a_name,

            "teamB": team_b_name,

            "venue": venue_name,

            "predictionDate": str(
                prediction_date
            ),

            "teamAWinProbability": round(
                probability_a,
                6,
            ),

            "teamBWinProbability": round(
                probability_b,
                6,
            ),

            "predictedWinner": predicted_winner,

            "modelVersion": model_package.get(
                "artifact_version"
            ),

            "modelType": model_package.get(
                "model_type"
            ),

            "featureSet": model_package.get(
                "feature_set"
            ),

            "featureCount": model_package.get(
                "feature_count"
            ),

            "teamAMatchesBefore": int(
                features[
                    "team_a_matches_before"
                ]
            ),

            "teamBMatchesBefore": int(
                features[
                    "team_b_matches_before"
                ]
            ),

            "headToHeadMatchesBefore": int(
                features[
                    "head_to_head_matches_before"
                ]
            ),

            "teamAVenueMatchesBefore": int(
                features[
                    "team_a_venue_matches_before"
                ]
            ),

            "teamBVenueMatchesBefore": int(
                features[
                    "team_b_venue_matches_before"
                ]
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:

        print()
        print("=" * 70)
        print("PREDICTION ERROR")
        print("=" * 70)
        print(
            type(exc).__name__,
            ":",
            str(exc),
        )
        print("=" * 70)
        print()

        raise HTTPException(
            status_code=500,
            detail=(
                "Prediction failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        )

    finally:

        connection.close()
