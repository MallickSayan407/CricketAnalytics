import { useEffect, useState } from "react";
import {
    getTeams,
    getVenues,
    simulateTournament,
    simulateSingleTournament,
} from "../services/api";
import "./TournamentSimulator.css";

const DEFAULT_TEAMS = [
    "India",
    "Australia",
    "England",
    "South Africa",
    "New Zealand",
    "Pakistan",
    "Sri Lanka",
    "Bangladesh",
];

function TournamentSimulator() {

    const [teams, setTeams] = useState([]);
    const [venues, setVenues] = useState([]);

    const [selectedTeams, setSelectedTeams] =
        useState(DEFAULT_TEAMS);

    const [venue, setVenue] =
        useState("Wankhede Stadium");

    const [predictionDate, setPredictionDate] =
        useState("2026-09-13");

    const [simulations, setSimulations] =
        useState(10000);

    const [result, setResult] =
        useState(null);
		
	const [singleTournament, setSingleTournament] =
		useState(null);

	const [singleLoading, setSingleLoading] =
		useState(false);

    const [loading, setLoading] =
        useState(false);

    const [error, setError] =
        useState("");

    useEffect(() => {

        const loadData = async () => {

            try {

                const [
                    teamsResponse,
                    venuesResponse
                ] = await Promise.all([
                    getTeams(),
                    getVenues(),
                ]);

                const teamData =
                    teamsResponse.data || [];

                const venueData =
                    venuesResponse.data || [];

                const uniqueTeams =
                    Array.from(
                        new Set(
                            teamData
                                .map(team => team.name)
                                .filter(Boolean)
                        )
                    ).sort();

                const uniqueVenues =
                    Array.from(
                        new Set(
                            venueData
                                .map(venue => venue.name)
                                .filter(Boolean)
                        )
                    ).sort();

                setTeams(uniqueTeams);
                setVenues(uniqueVenues);

                if (
                    uniqueVenues.includes(
                        "Wankhede Stadium"
                    )
                ) {
                    setVenue(
                        "Wankhede Stadium"
                    );
                } else if (
                    uniqueVenues.length > 0
                ) {
                    setVenue(
                        uniqueVenues[0]
                    );
                }

            } catch (err) {

                console.error(
                    "Could not load simulator data:",
                    err
                );

                setError(
                    "Could not load teams or venues."
                );
            }
        };

        loadData();

    }, []);

    const changeTeam = (
        index,
        newTeam
    ) => {

        setSelectedTeams(previous => {

            const updated = [
                ...previous
            ];

            updated[index] = newTeam;

            return updated;
        });

        setResult(null);
        setError("");
    };

    const resetTeams = () => {

        setSelectedTeams(
            DEFAULT_TEAMS
        );

        setResult(null);
        setError("");
    };

    const hasDuplicateTeams =
        new Set(selectedTeams).size !==
        selectedTeams.length;

    const handleSimulation = async () => {

        setError("");
        setResult(null);

        if (
            selectedTeams.length !== 8
        ) {

            setError(
                "Exactly 8 teams are required."
            );

            return;
        }

        if (hasDuplicateTeams) {

            setError(
                "Each team must be unique."
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

        try {

            setLoading(true);

            const request = {
                teams: selectedTeams,
                venue: venue,
                predictionDate:
                    predictionDate,
            };

            const response =
                await simulateTournament(
                    request,
                    simulations
                );

            setResult(
                response.data
            );

        } catch (err) {

            console.error(
                "Tournament simulation failed:",
                err
            );

            const message =
                err?.response?.data?.message ||
                err?.response?.data ||
                "Tournament simulation failed.";

            setError(
                typeof message === "string"
                    ? message
                    : "Tournament simulation failed."
            );

        } finally {

            setLoading(false);
        }
    };
	
	const handleSingleTournament = async () => {

	    setError("");
	    setSingleTournament(null);

	    if (
	        selectedTeams.length !== 8
	    ) {

	        setError(
	            "Exactly 8 teams are required."
	        );

	        return;
	    }

	    if (hasDuplicateTeams) {

	        setError(
	            "Each team must be unique."
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

	    try {

	        setSingleLoading(true);

	        const request = {
	            teams: selectedTeams,
	            venue: venue,
	            predictionDate:
	                predictionDate,
	        };

	        const response =
	            await simulateSingleTournament(
	                request
	            );

	        setSingleTournament(
	            response.data
	        );

	    } catch (err) {

	        console.error(
	            "Single tournament simulation failed:",
	            err
	        );

	        const message =
	            err?.response?.data?.message ||
	            err?.response?.data ||
	            "Single tournament simulation failed.";

	        setError(
	            typeof message === "string"
	                ? message
	                : "Single tournament simulation failed."
	        );

	    } finally {

	        setSingleLoading(false);
	    }
	};

    const champion =
        result?.results?.[0];

    return (
        <div className="tournament-page">

            {/* =====================================================
                HEADER
            ===================================================== */}

            <div className="tournament-header">

                <div>

                    <p className="eyebrow">
                        AI + Monte Carlo
                    </p>

                    <h1>
                        ODI Tournament Simulator
                    </h1>

                    <p className="subtitle">
                        Simulate thousands of tournament
                        outcomes using the ODI machine
                        learning prediction model.
                    </p>

                </div>

            </div>

            <div className="simulator-layout">

                {/* =================================================
                    LEFT — CONFIGURATION
                ================================================= */}

                <section className="config-card">

                    <div className="section-heading">

                        <div>

                            <h2>
                                Tournament setup
                            </h2>

                            <p>
                                Choose exactly 8 unique
                                teams for the tournament.
                            </p>

                        </div>

                        <button
                            type="button"
                            className="reset-button"
                            onClick={resetTeams}
                        >
                            Reset
                        </button>

                    </div>

                    {/* =================================================
                        TEAM SELECTORS
                    ================================================= */}

                    <div className="team-slots">

                        {selectedTeams.map(
                            (selectedTeam, index) => (

                                <div
                                    className="team-slot"
                                    key={index}
                                >

                                    <span className="team-slot-number">
                                        {index + 1}
                                    </span>

                                    <div className="team-slot-control">

                                        <label>
                                            Team {index + 1}
                                        </label>

                                        <select
                                            value={
                                                selectedTeam
                                            }
                                            onChange={event =>
                                                changeTeam(
                                                    index,
                                                    event.target.value
                                                )
                                            }
                                        >

                                            {teams
                                                .filter(team =>
                                                    team ===
                                                    selectedTeam ||
                                                    !selectedTeams.includes(
                                                        team
                                                    )
                                                )
                                                .map(team => (

                                                    <option
                                                        key={team}
                                                        value={team}
                                                    >
                                                        {team}
                                                    </option>

                                                ))
                                            }

                                        </select>

                                    </div>

                                </div>

                            )
                        )}

                    </div>

                    <div
                        className={
                            hasDuplicateTeams
                                ? "selection-count invalid"
                                : "selection-count"
                        }
                    >

                        {selectedTeams.length}
                        {" / "}
                        8 teams selected

                        {hasDuplicateTeams && (
                            <span>
                                {" "}• Duplicate team
                            </span>
                        )}

                    </div>

                    {/* =================================================
                        VENUE
                    ================================================= */}

                    <div className="form-grid">

                        <div className="form-group">

                            <label>
                                Venue
                            </label>

                            <select
                                value={venue}
                                onChange={event =>
                                    setVenue(
                                        event.target.value
                                    )
                                }
                            >

                                {venues.length === 0 ? (

                                    <option>
                                        Wankhede Stadium
                                    </option>

                                ) : (

                                    venues.map(
                                        venueName => (

                                            <option
                                                key={venueName}
                                                value={venueName}
                                            >
                                                {venueName}
                                            </option>

                                        )
                                    )

                                )}

                            </select>

                        </div>

                        {/* =================================================
                            DATE
                        ================================================= */}

                        <div className="form-group">

                            <label>
                                Prediction date
                            </label>

                            <input
                                type="date"
                                value={predictionDate}
                                onChange={event =>
                                    setPredictionDate(
                                        event.target.value
                                    )
                                }
                            />

                        </div>

                        {/* =================================================
                            SIMULATIONS
                        ================================================= */}

                        <div className="form-group">

                            <label>
                                Simulations
                            </label>

                            <select
                                value={simulations}
                                onChange={event =>
                                    setSimulations(
                                        Number(
                                            event.target.value
                                        )
                                    )
                                }
                            >

                                <option value={100}>
                                    100
                                </option>

                                <option value={1000}>
                                    1,000
                                </option>

                                <option value={5000}>
                                    5,000
                                </option>

                                <option value={10000}>
                                    10,000
                                </option>

                            </select>

                        </div>

                    </div>

                    {error && (
                        <div className="error-box">
                            {error}
                        </div>
                    )}

					<div className="simulation-actions">

					    <button
					        type="button"
					        className="simulate-button primary"
					        onClick={handleSimulation}
					        disabled={loading || singleLoading}
					    >

					        {loading
					            ? "Running Monte Carlo..."
					            : "Run Monte Carlo"}

					    </button>

					    <button
					        type="button"
					        className="simulate-button secondary"
					        onClick={handleSingleTournament}
					        disabled={loading || singleLoading}
					    >

					        {singleLoading
					            ? "Simulating Tournament..."
					            : "Run One Tournament"}

					    </button>

					</div>

                    {loading && (
                        <p className="loading-text">
                            Running{" "}
                            {simulations.toLocaleString()}
                            {" "}
                            tournament simulations...
                        </p>
                    )}

                </section>

                {/* =================================================
                    RIGHT — RESULTS
                ================================================= */}

                <section className="results-card">

                    {!result ? (

                        <div className="empty-state">

                            <div className="empty-icon">
                                🏆
                            </div>

                            <h2>
                                Ready to simulate
                            </h2>

                            <p>
                                Configure the tournament
                                and run the simulation to
                                see qualification and
                                championship probabilities.
                            </p>

                        </div>

                    ) : (

                        <>

                            <div className="results-heading">

                                <div>

                                    <p className="eyebrow">
                                        Simulation results
                                    </p>

                                    <h2>
                                        Tournament probabilities
                                    </h2>

                                </div>

                                <div className="simulation-count">
                                    {result.simulations?.toLocaleString()}
                                    {" "}
                                    simulations
                                </div>

                            </div>

                            {/* =================================================
                                CHAMPION CARD
                            ================================================= */}

                            {champion && (

                                <div className="champion-card">

                                    <div>

                                        <span>
                                            Most likely champion
                                        </span>

                                        <strong>
                                            {champion.team}
                                        </strong>

                                        <small>
                                            Won{" "}
                                            {champion.tournamentWins?.toLocaleString()}
                                            {" "}
                                            of{" "}
                                            {result.simulations?.toLocaleString()}
                                            {" "}
                                            simulations
                                        </small>

                                    </div>

                                    <div className="champion-probability">

                                        {champion
                                            .championshipProbability
                                            .toFixed(2)}

                                        %

                                    </div>

                                </div>

                            )}

                            {/* =================================================
                                LEGEND
                            ================================================= */}

                            <div className="probability-legend">

                                <span>
                                    Qualification
                                </span>

                                <span>
                                    Championship
                                </span>

                            </div>

							{/* =================================================
							    TEAM RESULTS
							================================================= */}

							<div className="probability-list">

							    {result.results?.map(
							        (item, index) => (

							            <div
							                className="probability-row"
							                key={item.team}
							            >

							                <div className="rank">
							                    {index + 1}
							                </div>

							                <div className="team-name">
							                    {item.team}
							                </div>

							                <div className="probability-bars">

							                    {/* Qualification */}

							                    <div className="metric-bar">

							                        <div className="metric-label">
							                            QUALIFY
							                        </div>

							                        <div className="probability-track">

							                            <div
							                                className="probability-fill qualification-fill"
							                                style={{
							                                    width:
							                                        `${item.qualificationProbability}%`,
							                                }}
							                            />

							                        </div>

							                        <div className="metric-value">

							                            {item
							                                .qualificationProbability
							                                .toFixed(2)}
							                            %

							                        </div>

							                    </div>

							                    {/* Final */}

							                    <div className="metric-bar">

							                        <div className="metric-label">
							                            FINAL
							                        </div>

							                        <div className="probability-track">

							                            <div
							                                className="probability-fill final-fill"
							                                style={{
							                                    width:
							                                        `${item.finalAppearanceProbability}%`,
							                                }}
							                            />

							                        </div>

							                        <div className="metric-value">

							                            {item
							                                .finalAppearanceProbability
							                                .toFixed(2)}
							                            %

							                        </div>

							                    </div>

							                    {/* Championship */}

							                    <div className="metric-bar">

							                        <div className="metric-label">
							                            CHAMPION
							                        </div>

							                        <div className="probability-track">

							                            <div className="probability-fill championship-fill"
							                                style={{
							                                    width:
							                                        `${item.championshipProbability}%`,
							                                }}
							                            />

							                        </div>

							                        <div className="metric-value">

							                            {item
							                                .championshipProbability
							                                .toFixed(2)}
							                            %

							                        </div>

							                    </div>

							                </div>

							            </div>

							        )
							    )}

							</div>
							
							{/* =================================================
							    FINISH POSITION ANALYTICS
							================================================= */}

							<div className="finish-section">

							    <div className="finish-section-header">

							        <div>

							            <p className="eyebrow">
							                League finish
							            </p>

							            <h3>
							                Most likely finishing positions
							            </h3>

							        </div>

							    </div>

							    <div className="finish-grid">

							        {result.results?.map(item => (

							            <div
							                className="finish-card"
							                key={item.team}
							            >

							                <div className="finish-team">
							                    {item.team}
							                </div>

							                <div className="finish-position">

							                    <div>
							                        <span>1st</span>
							                        <strong>
							                            {item.firstPlaceProbability.toFixed(1)}%
							                        </strong>
							                    </div>

							                    <div>
							                        <span>2nd</span>
							                        <strong>
							                            {item.secondPlaceProbability.toFixed(1)}%
							                        </strong>
							                    </div>

							                    <div>
							                        <span>3rd</span>
							                        <strong>
							                            {item.thirdPlaceProbability.toFixed(1)}%
							                        </strong>
							                    </div>

							                    <div>
							                        <span>4th</span>
							                        <strong>
							                            {item.fourthPlaceProbability.toFixed(1)}%
							                        </strong>
							                    </div>

							                </div>

							            </div>

							        ))}

							    </div>

							</div>

                        </>

                    )}
					
					{/* =================================================
					    SINGLE TOURNAMENT RESULT
					================================================= */}

					{singleTournament && (

					    <div className="single-tournament-section">

					        <div className="single-tournament-header">

					            <div>

					                <p className="eyebrow">
					                    One simulated tournament
					                </p>

					                <h3>
					                    Playoff bracket
					                </h3>

					            </div>

					            <div className="champion-badge">
					                🏆 {singleTournament.champion}
					            </div>

					        </div>

					        {/* ==========================================
					            LEAGUE TABLE
					        ========================================== */}

					        <div className="league-result">

					            <h4>
					                League standings
					            </h4>

					            <div className="league-table">

					                <div className="league-table-header">

					                    <span>#</span>
					                    <span>Team</span>
					                    <span>MP</span>
					                    <span>W</span>
					                    <span>L</span>
					                    <span>Pts</span>

					                </div>

					                {singleTournament.standings?.map(
					                    (team, index) => (

					                        <div
					                            className={
					                                index < 4
					                                    ? "league-table-row qualified"
					                                    : "league-table-row"
					                            }
					                            key={team.team}
					                        >

					                            <span>
					                                {index + 1}
					                            </span>

					                            <strong>
					                                {team.team}
					                            </strong>

					                            <span>
					                                {team.matches}
					                            </span>

					                            <span>
					                                {team.wins}
					                            </span>

					                            <span>
					                                {team.losses}
					                            </span>

					                            <strong>
					                                {team.points}
					                            </strong>

					                        </div>

					                    )
					                )}

					            </div>

					        </div>

					        {/* ==========================================
					            PLAYOFF BRACKET
					        ========================================== */}

					        <div className="playoff-bracket">

					            <div className="bracket-stage">

					                <h4>
					                    Semifinals
					                </h4>

					                <div className="playoff-match">

					                    <span>
					                        {singleTournament
					                            .semiFinal1
					                            .teamA}
					                    </span>

					                    <strong>
					                        {singleTournament
					                            .semiFinal1
					                            .winner}
					                    </strong>

					                    <span>
					                        {singleTournament
					                            .semiFinal1
					                            .teamB}
					                    </span>

					                </div>

					                <div className="match-probability">

					                    {(
					                        singleTournament
					                            .semiFinal1
					                            .teamAWinProbability
					                        * 100
					                    ).toFixed(0)}
					                    %
					                    {" "}
					                    vs
					                    {" "}
					                    {(
					                        singleTournament
					                            .semiFinal1
					                            .teamBWinProbability
					                        * 100
					                    ).toFixed(0)}
					                    %

					                </div>

					                <div className="playoff-match">

					                    <span>
					                        {singleTournament
					                            .semiFinal2
					                            .teamA}
					                    </span>

					                    <strong>
					                        {singleTournament
					                            .semiFinal2
					                            .winner}
					                    </strong>

					                    <span>
					                        {singleTournament
					                            .semiFinal2
					                            .teamB}
					                    </span>

					                </div>

					                <div className="match-probability">

					                    {(
					                        singleTournament
					                            .semiFinal2
					                            .teamAWinProbability
					                        * 100
					                    ).toFixed(0)}
					                    %
					                    {" "}
					                    vs
					                    {" "}
					                    {(
					                        singleTournament
					                            .semiFinal2
					                            .teamBWinProbability
					                        * 100
					                    ).toFixed(0)}
					                    %

					                </div>

					            </div>

					            <div className="bracket-arrow">
					                →
					            </div>

					            <div className="bracket-stage final-stage">

					                <h4>
					                    Final
					                </h4>

					                <div className="final-match">

					                    <span>
					                        {singleTournament
					                            .finalMatch
					                            .teamA}
					                    </span>

					                    <strong>
					                        {singleTournament
					                            .finalMatch
					                            .winner}
					                    </strong>

					                    <span>
					                        {singleTournament
					                            .finalMatch
					                            .teamB}
					                    </span>

					                </div>

					                <div className="match-probability">

					                    {(
					                        singleTournament
					                            .finalMatch
					                            .teamAWinProbability
					                        * 100
					                    ).toFixed(0)}
					                    %
					                    {" "}
					                    vs
					                    {" "}
					                    {(
					                        singleTournament
					                            .finalMatch
					                            .teamBWinProbability
					                        * 100
					                    ).toFixed(0)}
					                    %

					                </div>

					            </div>

					        </div>

					        {/* ==========================================
					            CHAMPION
					        ========================================== */}

					        <div className="tournament-champion">

					            <span>
					                Tournament Champion
					            </span>

					            <strong>
					                🏆 {singleTournament.champion}
					            </strong>

					        </div>

					    </div>

					)}

                </section>

            </div>

        </div>
    );
}

export default TournamentSimulator;