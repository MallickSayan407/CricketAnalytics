import { useEffect, useState } from "react";
import api from "../services/api";
import "./Predictor.css";

function getTodayDate() {
    const today = new Date();

    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, "0");
    const day = String(today.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}

function Predictor() {

    // =========================================================
    // STATE
    // =========================================================

    const [teams, setTeams] = useState([]);
    const [venues, setVenues] = useState([]);

    const [teamA, setTeamA] = useState("India");
    const [teamB, setTeamB] = useState("Australia");
    const [venue, setVenue] = useState("Wankhede Stadium");

    const [predictionDate, setPredictionDate] = useState(
        getTodayDate()
    );

    const [prediction, setPrediction] = useState(null);

    const [loading, setLoading] = useState(false);
    const [loadingData, setLoadingData] = useState(true);

    const [error, setError] = useState("");
    const [dataError, setDataError] = useState("");


    // =========================================================
    // LOAD TEAMS + VENUES
    // =========================================================

    useEffect(() => {

        const loadData = async () => {

            try {

                setLoadingData(true);
                setDataError("");

                const [teamsResponse, venuesResponse] =
                    await Promise.all([
                        api.get("/teams"),
                        api.get("/venues"),
                    ]);


                // -------------------------------------------------
                // TEAMS
                // -------------------------------------------------

                const teamData = Array.isArray(teamsResponse.data)
                    ? teamsResponse.data
                    : [];

                /*
                 * The database contains separate team records
                 * for different cricket contexts/genders.
                 *
                 * The predictor only needs unique team names.
                 */

                const uniqueTeams = [
                    ...new Map(
                        teamData
                            .filter(
                                (team) =>
                                    team.name &&
                                    team.name.trim() !== ""
                            )
                            .map((team) => [
                                team.name.trim(),
                                team,
                            ])
                    ).values(),
                ].sort((a, b) =>
                    a.name.localeCompare(b.name)
                );


                // -------------------------------------------------
                // VENUES
                // -------------------------------------------------

                const venueData = Array.isArray(venuesResponse.data)
                    ? venuesResponse.data
                    : [];

                /*
                 * Several historical venue names are duplicated
                 * or represented by slightly different records.
                 *
                 * We remove exact duplicate names for the dropdown.
                 */

                const uniqueVenues = [
                    ...new Map(
                        venueData
                            .filter(
                                (item) =>
                                    item.name &&
                                    item.name.trim() !== ""
                            )
                            .map((item) => [
                                item.name.trim(),
                                item,
                            ])
                    ).values(),
                ].sort((a, b) =>
                    a.name.localeCompare(b.name)
                );


                setTeams(uniqueTeams);
                setVenues(uniqueVenues);


                // -------------------------------------------------
                // DEFAULT TEAM SELECTION
                // -------------------------------------------------

                if (
                    !uniqueTeams.some(
                        (team) => team.name === teamA
                    )
                ) {
                    setTeamA(
                        uniqueTeams.length > 0
                            ? uniqueTeams[0].name
                            : ""
                    );
                }

                if (
                    !uniqueTeams.some(
                        (team) => team.name === teamB
                    )
                ) {
                    setTeamB(
                        uniqueTeams.length > 1
                            ? uniqueTeams[1].name
                            : ""
                    );
                }


                // -------------------------------------------------
                // DEFAULT VENUE SELECTION
                // -------------------------------------------------

                if (
                    !uniqueVenues.some(
                        (item) => item.name === venue
                    )
                ) {
                    setVenue(
                        uniqueVenues.length > 0
                            ? uniqueVenues[0].name
                            : ""
                    );
                }

            } catch (err) {

                console.error(
                    "Failed to load predictor data:",
                    err
                );

                setDataError(
                    "Unable to load teams and venues. Please make sure the Spring Boot backend is running."
                );

            } finally {

                setLoadingData(false);

            }
        };


        loadData();

    }, []);


    // =========================================================
    // PREDICT MATCH
    // =========================================================

    const handlePredict = async (event) => {

        event.preventDefault();

        setError("");
        setPrediction(null);


        // -------------------------------------------------
        // VALIDATION
        // -------------------------------------------------

        if (!teamA || !teamB) {

            setError(
                "Please select both teams."
            );

            return;
        }


        if (teamA === teamB) {

            setError(
                "Team A and Team B must be different."
            );

            return;
        }


        if (!venue) {

            setError(
                "Please select a venue."
            );

            return;
        }


        if (!predictionDate) {

            setError(
                "Please select a prediction date."
            );

            return;
        }


        // -------------------------------------------------
        // API REQUEST
        // -------------------------------------------------

        setLoading(true);

        try {

            const response = await api.post(
                "/ml/predict/odi",
                {
                    teamA,
                    teamB,
                    venue,
                    predictionDate,
                }
            );


            setPrediction(response.data);

        } catch (err) {

            console.error(
                "Prediction error:",
                err
            );


            if (err.response?.data?.message) {

                setError(
                    err.response.data.message
                );

            } else if (err.response?.data?.error) {

                setError(
                    err.response.data.error
                );

            } else {

                setError(
                    "Unable to generate prediction. Please make sure the backend and ML API are running."
                );

            }

        } finally {

            setLoading(false);

        }

    };


    // =========================================================
    // RENDER
    // =========================================================

    return (

        <div className="predictor-page">

            {/* =================================================
                HEADER
            ================================================= */}

            <div className="predictor-header">

                <div>

                    <p className="predictor-eyebrow">
                        AI / ML ANALYTICS
                    </p>

                    <h1>
                        ODI Match Predictor
                    </h1>

                    <p className="predictor-subtitle">
                        Predict the winner of an ODI match using
                        historical team performance, venue records
                        and head-to-head statistics.
                    </p>

                </div>

            </div>


            {/* =================================================
                GRID
            ================================================= */}

            <div className="predictor-grid">


                {/* =================================================
                    PREDICTION FORM
                ================================================= */}

                <section className="prediction-card">

                    <h2>
                        Match Configuration
                    </h2>


                    {/* DATA LOADING */}
                    {loadingData && (

                        <div className="prediction-loading-data">
                            Loading teams and venues...
                        </div>

                    )}


                    {/* DATA ERROR */}
                    {dataError && (

                        <div className="prediction-error">
                            {dataError}
                        </div>

                    )}


                    <form onSubmit={handlePredict}>


                        {/* =========================================
                            TEAM SELECTION
                        ========================================= */}

                        <div className="team-selection">


                            {/* TEAM A */}

                            <div className="form-group">

                                <label>
                                    Team A
                                </label>

                                <select
                                    value={teamA}
                                    onChange={(e) =>
                                        setTeamA(
                                            e.target.value
                                        )
                                    }
                                    disabled={
                                        loadingData ||
                                        teams.length === 0
                                    }
                                >

                                    {teams.map((team) => (

                                        <option
                                            key={team.id}
                                            value={team.name}
                                        >
                                            {team.name}
                                        </option>

                                    ))}

                                </select>

                            </div>


                            {/* VS */}

                            <div className="vs">

                                <span>
                                    VS
                                </span>

                            </div>


                            {/* TEAM B */}

                            <div className="form-group">

                                <label>
                                    Team B
                                </label>

                                <select
                                    value={teamB}
                                    onChange={(e) =>
                                        setTeamB(
                                            e.target.value
                                        )
                                    }
                                    disabled={
                                        loadingData ||
                                        teams.length === 0
                                    }
                                >

                                    {teams.map((team) => (

                                        <option
                                            key={team.id}
                                            value={team.name}
                                        >
                                            {team.name}
                                        </option>

                                    ))}

                                </select>

                            </div>

                        </div>


                        {/* =========================================
                            VENUE
                        ========================================= */}

                        <div className="form-group">

                            <label>
                                Venue
                            </label>

                            <select
                                value={venue}
                                onChange={(e) =>
                                    setVenue(
                                        e.target.value
                                    )
                                }
                                disabled={
                                    loadingData ||
                                    venues.length === 0
                                }
                            >

                                {venues.map((item) => (

                                    <option
                                        key={item.id}
                                        value={item.name}
                                    >
                                        {item.name}
                                    </option>

                                ))}

                            </select>

                        </div>


                        {/* =========================================
                            DATE
                        ========================================= */}

                        <div className="form-group">

                            <label>
                                Prediction Date
                            </label>

                            <input
                                type="date"
                                value={predictionDate}
                                onChange={(e) =>
                                    setPredictionDate(
                                        e.target.value
                                    )
                                }
                            />

                        </div>


                        {/* =========================================
                            ERROR
                        ========================================= */}

                        {error && (

                            <div className="prediction-error">
                                {error}
                            </div>

                        )}


                        {/* =========================================
                            BUTTON
                        ========================================= */}

                        <button
                            type="submit"
                            className="predict-button"
                            disabled={
                                loading ||
                                loadingData ||
                                teams.length === 0 ||
                                venues.length === 0
                            }
                        >

                            {loading
                                ? "Analyzing Match..."
                                : "Predict Match"}

                        </button>

                    </form>

                </section>


                {/* =================================================
                    RESULT
                ================================================= */}

                <section className="prediction-result">


                    {/* =========================================
                        EMPTY STATE
                    ========================================= */}

                    {!prediction && !loading && (

                        <div className="empty-result">

                            <div className="empty-icon">
                                🏏
                            </div>

                            <h2>
                                Prediction Ready
                            </h2>

                            <p>
                                Select the teams, venue and date,
                                then click{" "}
                                <strong>
                                    Predict Match
                                </strong>{" "}
                                to generate an AI-powered ODI
                                prediction.
                            </p>

                        </div>

                    )}


                    {/* =========================================
                        LOADING
                    ========================================= */}

                    {loading && (

                        <div className="loading-result">

                            <div className="loader"></div>

                            <h2>
                                Analyzing Match...
                            </h2>

                            <p>
                                Evaluating historical performance,
                                recent form, venue records and
                                head-to-head data.
                            </p>

                        </div>

                    )}


                    {/* =========================================
                        RESULT
                    ========================================= */}

                    {prediction && !loading && (

                        <div className="result-content">


                            <p className="result-eyebrow">
                                MODEL PREDICTION
                            </p>


                            <h2>
                                {prediction.predictedWinner}
                            </h2>


                            <p className="winner-text">
                                predicted to win
                            </p>


                            {/* =====================================
                                PROBABILITIES
                            ===================================== */}

                            <div className="probability-container">


                                {/* TEAM A */}

                                <div className="probability-header">

                                    <span>
                                        {prediction.teamA}
                                    </span>

                                    <strong>
                                        {(
                                            prediction.teamAWinProbability *
                                            100
                                        ).toFixed(2)}
                                        %
                                    </strong>

                                </div>


                                <div className="probability-bar">

                                    <div
                                        className="probability-a"
                                        style={{
                                            width:
                                                `${prediction.teamAWinProbability * 100}%`,
                                        }}
                                    ></div>

                                </div>


                                {/* TEAM B */}

                                <div className="probability-header">

                                    <span>
                                        {prediction.teamB}
                                    </span>

                                    <strong>
                                        {(
                                            prediction.teamBWinProbability *
                                            100
                                        ).toFixed(2)}
                                        %
                                    </strong>

                                </div>


                                <div className="probability-bar">

                                    <div
                                        className="probability-b"
                                        style={{
                                            width:
                                                `${prediction.teamBWinProbability * 100}%`,
                                        }}
                                    ></div>

                                </div>

                            </div>


                            {/* =====================================
                                MATCH SUMMARY
                            ===================================== */}

                            <div className="match-summary">


                                <div>

                                    <span>
                                        Venue
                                    </span>

                                    <strong>
                                        {prediction.venue}
                                    </strong>

                                </div>


                                <div>

                                    <span>
                                        Head-to-Head
                                    </span>

                                    <strong>
                                        {prediction.headToHeadMatchesBefore}
                                    </strong>

                                </div>


                                <div>

                                    <span>
                                        {prediction.teamA} matches
                                    </span>

                                    <strong>
                                        {prediction.teamAMatchesBefore}
                                    </strong>

                                </div>


                                <div>

                                    <span>
                                        {prediction.teamB} matches
                                    </span>

                                    <strong>
                                        {prediction.teamBMatchesBefore}
                                    </strong>

                                </div>

                            </div>


                            {/* =====================================
                                MODEL INFORMATION
                            ===================================== */}

                            <div className="model-info">


                                <span>
                                    Model
                                </span>

                                <strong>
                                    {prediction.modelType}
                                </strong>


                                <span>
                                    Feature Set
                                </span>

                                <strong>
                                    {prediction.featureSet}
                                </strong>


                                <span>
                                    Features
                                </span>

                                <strong>
                                    {prediction.featureCount}
                                </strong>

                            </div>

                        </div>

                    )}

                </section>

            </div>

        </div>

    );
}

export default Predictor;