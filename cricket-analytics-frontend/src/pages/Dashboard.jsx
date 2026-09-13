import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../services/api";
import StatCard from "../components/StatCard";

import "./Dashboard.css";

function Dashboard() {

    const [topRunScorers, setTopRunScorers] = useState([]);
    const [topWicketTakers, setTopWicketTakers] = useState([]);

    const [playerCount, setPlayerCount] = useState(0);
    const [teamCount, setTeamCount] = useState(0);
    const [matchCount, setMatchCount] = useState(0);
    const [competitionCount, setCompetitionCount] = useState(0);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");


    useEffect(() => {

        const fetchDashboardData = async () => {

            try {

                setLoading(true);
                setError("");


                const [
                    playersResponse,
                    teamsResponse,
                    matchesResponse,
                    competitionsResponse,
                    runsResponse,
                    wicketsResponse
                ] = await Promise.all([

                    api.get("/players"),

                    api.get("/teams"),

                    api.get("/matches"),

                    api.get("/competitions"),

                    api.get(
                        "/analytics/leaderboard/runs"
                    ),

                    api.get(
                        "/analytics/leaderboard/wickets"
                    )
                ]);


                /*
                 * -------------------------------------------------
                 * PLATFORM COUNTS
                 * -------------------------------------------------
                 */

                setPlayerCount(
                    Array.isArray(playersResponse.data)
                        ? playersResponse.data.length
                        : 0
                );


                setTeamCount(
                    Array.isArray(teamsResponse.data)
                        ? teamsResponse.data.length
                        : 0
                );


                setMatchCount(
                    Array.isArray(matchesResponse.data)
                        ? matchesResponse.data.length
                        : 0
                );


                setCompetitionCount(
                    Array.isArray(competitionsResponse.data)
                        ? competitionsResponse.data.length
                        : 0
                );


                /*
                 * -------------------------------------------------
                 * TOP RUN SCORERS
                 * -------------------------------------------------
                 */

                setTopRunScorers(
                    Array.isArray(runsResponse.data)
                        ? runsResponse.data.slice(0, 5)
                        : []
                );


                /*
                 * -------------------------------------------------
                 * TOP WICKET TAKERS
                 * -------------------------------------------------
                 */

                setTopWicketTakers(
                    Array.isArray(wicketsResponse.data)
                        ? wicketsResponse.data.slice(0, 5)
                        : []
                );

            } catch (err) {

                console.error(
                    "Failed to load dashboard data:",
                    err
                );

                setError(
                    "Unable to load dashboard data from the backend."
                );

            } finally {

                setLoading(false);
            }
        };


        fetchDashboardData();

    }, []);


    return (

        <main className="dashboard-page">


            {/* =================================================
                HERO
                ================================================= */}

            <section className="dashboard-hero">

                <div className="dashboard-hero-content">

                    <p className="dashboard-eyebrow">
                        INTERNATIONAL • IPL • ANALYTICS
                    </p>

                    <h1>
                        Cricket
                        <br />
                        Analytics
                    </h1>

                    <p className="dashboard-hero-description">
                        Explore cricket through data.
                        Analyze players, teams, matches,
                        venues, seasons and performance trends
                        across international cricket and the IPL.
                    </p>


                    <div className="dashboard-hero-actions">

                        <Link
                            to="/players"
                            className="dashboard-primary-button"
                        >
                            Explore Players
                        </Link>

                        <Link
                            to="/teams"
                            className="dashboard-secondary-button"
                        >
                            Explore Teams
                        </Link>

                    </div>

                </div>

            </section>


            {/* =================================================
                ERROR
                ================================================= */}

            {error && (

                <div className="dashboard-error">
                    {error}
                </div>

            )}


            {/* =================================================
                PLATFORM STATISTICS
                ================================================= */}

            <section className="dashboard-statistics">

                <StatCard
                    label="Players"
                    value={loading ? "—" : playerCount}
                    description="Registered players"
                />

                <StatCard
                    label="Teams"
                    value={loading ? "—" : teamCount}
                    description="International & league teams"
                />

                <StatCard
                    label="Matches"
                    value={loading ? "—" : matchCount}
                    description="Recorded matches"
                />

                <StatCard
                    label="Competitions"
                    value={loading ? "—" : competitionCount}
                    description="Available competitions"
                />

            </section>


            {/* =================================================
                TOP RUN SCORERS
                ================================================= */}

            <section className="dashboard-section">

                <div className="dashboard-section-header">

                    <div>

                        <p className="dashboard-section-eyebrow">
                            CAREER LEADERBOARD
                        </p>

                        <h2>
                            Top Run Scorers
                        </h2>

                        <p>
                            The highest run scorers in the
                            current analytics database.
                        </p>

                    </div>

                    <Link
                        to="/leaderboards"
                        className="dashboard-section-link"
                    >
                        View leaderboard →
                    </Link>

                </div>


                {loading && (

                    <div className="dashboard-status">
                        Loading batting leaders...
                    </div>

                )}


                {!loading &&
                    !error &&
                    topRunScorers.length === 0 && (

                        <div className="dashboard-status">
                            No batting statistics available.
                        </div>

                    )}


                {!loading &&
                    topRunScorers.length > 0 && (

                        <div className="dashboard-leaderboard">

                            {topRunScorers.map((player, index) => (

                                <Link
                                    to={`/players/${player.playerId}`}
                                    className="dashboard-player-row"
                                    key={player.playerId}
                                >

                                    <div className="dashboard-rank">
                                        {String(
                                            player.rank ?? index + 1
                                        ).padStart(2, "0")}
                                    </div>


                                    <div className="dashboard-player-info">

                                        <strong>
                                            {player.playerName}
                                        </strong>

                                        <span>
                                            {player.teamName || "—"}
                                            {" • "}
                                            {player.playerRole || "Player"}
                                        </span>

                                    </div>


                                    <div className="dashboard-player-stat">

                                        <strong>
                                            {player.runs?.toLocaleString() ?? 0}
                                        </strong>

                                        <span>
                                            RUNS
                                        </span>

                                    </div>


                                    <div className="dashboard-player-stat">

                                        <strong>
                                            {player.battingAverage?.toFixed(2) ?? "—"}
                                        </strong>

                                        <span>
                                            AVERAGE
                                        </span>

                                    </div>


                                    <div className="dashboard-player-stat">

                                        <strong>
                                            {player.strikeRate?.toFixed(2) ?? "—"}
                                        </strong>

                                        <span>
                                            STRIKE RATE
                                        </span>

                                    </div>

                                </Link>

                            ))}

                        </div>

                    )}

            </section>


            {/* =================================================
                TOP WICKET TAKERS
                ================================================= */}

            <section className="dashboard-section">

                <div className="dashboard-section-header">

                    <div>

                        <p className="dashboard-section-eyebrow">
                            BOWLING LEADERBOARD
                        </p>

                        <h2>
                            Top Wicket Takers
                        </h2>

                        <p>
                            The leading wicket takers across
                            the available cricket data.
                        </p>

                    </div>

                    <Link
                        to="/leaderboards"
                        className="dashboard-section-link"
                    >
                        View leaderboard →
                    </Link>

                </div>


                {loading && (

                    <div className="dashboard-status">
                        Loading bowling leaders...
                    </div>

                )}


                {!loading &&
                    !error &&
                    topWicketTakers.length === 0 && (

                        <div className="dashboard-status">
                            No bowling statistics available.
                        </div>

                    )}


                {!loading &&
                    topWicketTakers.length > 0 && (

                        <div className="dashboard-leaderboard">

                            {topWicketTakers.map((player, index) => (

                                <Link
                                    to={`/players/${player.playerId}`}
                                    className="dashboard-player-row"
                                    key={player.playerId}
                                >

                                    <div className="dashboard-rank">
                                        {String(
                                            player.rank ?? index + 1
                                        ).padStart(2, "0")}
                                    </div>


                                    <div className="dashboard-player-info">

                                        <strong>
                                            {player.playerName}
                                        </strong>

                                        <span>
                                            {player.teamName || "—"}
                                            {" • "}
                                            {player.playerRole || "Player"}
                                        </span>

                                    </div>


                                    <div className="dashboard-player-stat dashboard-primary-stat">

                                        <strong>
                                            {player.wickets?.toLocaleString() ?? 0}
                                        </strong>

                                        <span>
                                            WICKETS
                                        </span>

                                    </div>


                                    <div className="dashboard-player-stat">

                                        <strong>
                                            {player.bowlingAverage?.toFixed(2) ?? "—"}
                                        </strong>

                                        <span>
                                            AVERAGE
                                        </span>

                                    </div>


                                    <div className="dashboard-player-stat">

                                        <strong>
                                            {player.economy?.toFixed(2) ?? "—"}
                                        </strong>

                                        <span>
                                            ECONOMY
                                        </span>

                                    </div>

                                </Link>

                            ))}

                        </div>

                    )}

            </section>


            {/* =================================================
                ANALYTICS EXPLORER
                ================================================= */}

            <section className="dashboard-section dashboard-explorer-section">

                <div className="dashboard-section-header">

                    <div>

                        <p className="dashboard-section-eyebrow">
                            EXPLORE THE PLATFORM
                        </p>

                        <h2>
                            Analytics Explorer
                        </h2>

                        <p>
                            Go deeper into the cricket data.
                        </p>

                    </div>

                </div>


                <div className="dashboard-explorer-grid">

                    <Link
                        to="/players"
                        className="dashboard-explorer-card"
                    >
                        <span>01</span>
                        <strong>Players</strong>
                        <p>
                            Profiles, statistics, form and trends.
                        </p>
                        <b>→</b>
                    </Link>


                    <Link
                        to="/teams"
                        className="dashboard-explorer-card"
                    >
                        <span>02</span>
                        <strong>Teams</strong>
                        <p>
                            Team records, scoring and performance.
                        </p>
                        <b>→</b>
                    </Link>


                    <Link
                        to="/matches"
                        className="dashboard-explorer-card"
                    >
                        <span>03</span>
                        <strong>Matches</strong>
                        <p>
                            Scorecards and match-level analytics.
                        </p>
                        <b>→</b>
                    </Link>


                    <Link
                        to="/venues"
                        className="dashboard-explorer-card"
                    >
                        <span>04</span>
                        <strong>Venues</strong>
                        <p>
                            Ground statistics and team performance.
                        </p>
                        <b>→</b>
                    </Link>


                    <Link
                        to="/seasons"
                        className="dashboard-explorer-card"
                    >
                        <span>05</span>
                        <strong>Seasons</strong>
                        <p>
                            Standings and season performance.
                        </p>
                        <b>→</b>
                    </Link>


                    <Link
                        to="/player-comparison"
                        className="dashboard-explorer-card"
                    >
                        <span>06</span>
                        <strong>Compare</strong>
                        <p>
                            Compare two players across contexts.
                        </p>
                        <b>→</b>
                    </Link>

                </div>

            </section>


        </main>
    );
}

export default Dashboard;