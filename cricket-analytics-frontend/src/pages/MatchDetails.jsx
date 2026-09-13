import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api from "../services/api";

function MatchDetails() {
    const { matchId } = useParams();

    const [match, setMatch] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchMatchAnalytics();
    }, [matchId]);

    const fetchMatchAnalytics = async () => {
        try {
            setLoading(true);
            setError("");

            const response = await api.get(
                `/analytics/matches/${matchId}`
            );

            setMatch(response.data);
        } catch (err) {
            console.error("Error fetching match analytics:", err);
            setError("Unable to load match details.");
        } finally {
            setLoading(false);
        }
    };

    const formatDate = (date) => {
        if (!date) {
            return "Date unavailable";
        }

        return new Date(date).toLocaleDateString("en-IN", {
            day: "2-digit",
            month: "short",
            year: "numeric",
        });
    };

    const formatNumber = (value) => {
        if (value === null || value === undefined) {
            return "0";
        }

        return value;
    };

    const formatDecimal = (value) => {
        if (value === null || value === undefined) {
            return "0.00";
        }

        return Number(value).toFixed(2);
    };

    const team1 = match?.team1;
    const team2 = match?.team2;

    const team1Players = useMemo(() => {
        if (!match?.playerPerformances || !team1?.teamName) {
            return [];
        }

        return match.playerPerformances.filter(
            (player) => player.teamName === team1.teamName
        );
    }, [match, team1]);

    const team2Players = useMemo(() => {
        if (!match?.playerPerformances || !team2?.teamName) {
            return [];
        }

        return match.playerPerformances.filter(
            (player) => player.teamName === team2.teamName
        );
    }, [match, team2]);

    const getBatters = (players) => {
        return players.filter(
            (player) =>
                player.ballsFaced > 0 ||
                player.battingRuns > 0 ||
                player.fours > 0 ||
                player.sixes > 0
        );
    };

    const getBowlers = (players) => {
        return players.filter(
            (player) =>
                player.ballsBowled > 0 ||
                player.wickets > 0 ||
                player.runsConceded > 0
        );
    };

    const renderBattingTable = (players) => {
        const batters = getBatters(players);

        if (batters.length === 0) {
            return (
                <div className="empty-state">
                    <p>No batting data available.</p>
                </div>
            );
        }

        return (
            <div className="table-container">
                <table className="analytics-table match-scorecard-table">
                    <thead>
                        <tr>
                            <th>Batter</th>
                            <th>R</th>
                            <th>B</th>
                            <th>4s</th>
                            <th>6s</th>
                            <th>SR</th>
                            <th>Status</th>
                        </tr>
                    </thead>

                    <tbody>
                        {batters.map((player) => (
                            <tr key={player.playerId}>
                                <td>
                                    <Link
                                        to={`/players/${player.playerId}`}
                                        className="table-player-link"
                                    >
                                        {player.playerName}
                                    </Link>
                                </td>

                                <td>
                                    <strong>
                                        {formatNumber(
                                            player.battingRuns
                                        )}
                                    </strong>
                                </td>

                                <td>
                                    {formatNumber(
                                        player.ballsFaced
                                    )}
                                </td>

                                <td>
                                    {formatNumber(player.fours)}
                                </td>

                                <td>
                                    {formatNumber(player.sixes)}
                                </td>

                                <td>
                                    {formatDecimal(
                                        player.battingStrikeRate
                                    )}
                                </td>

                                <td>
                                    {player.notOut ? "Not Out" : "Out"}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    const renderBowlingTable = (players) => {
        const bowlers = getBowlers(players);

        if (bowlers.length === 0) {
            return (
                <div className="empty-state">
                    <p>No bowling data available.</p>
                </div>
            );
        }

        return (
            <div className="table-container">
                <table className="analytics-table match-scorecard-table">
                    <thead>
                        <tr>
                            <th>Bowler</th>
                            <th>O</th>
                            <th>R</th>
                            <th>W</th>
                            <th>Econ</th>
                            <th>M</th>
                        </tr>
                    </thead>

                    <tbody>
                        {bowlers.map((player) => (
                            <tr key={player.playerId}>
                                <td>
                                    <Link
                                        to={`/players/${player.playerId}`}
                                        className="table-player-link"
                                    >
                                        {player.playerName}
                                    </Link>
                                </td>

                                <td>
                                    {player.oversBowled || "0.0"}
                                </td>

                                <td>
                                    {formatNumber(
                                        player.runsConceded
                                    )}
                                </td>

                                <td>
                                    <strong>
                                        {formatNumber(player.wickets)}
                                    </strong>
                                </td>

                                <td>
                                    {formatDecimal(
                                        player.bowlingEconomy
                                    )}
                                </td>

                                <td>
                                    {formatNumber(player.maidens)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="page-container">
                <div className="loading-state">
                    <h1>Match Details</h1>
                    <p>Loading match analytics...</p>
                </div>
            </div>
        );
    }

    if (error || !match) {
        return (
            <div className="page-container">
                <div className="page-header">
                    <div>
                        <h1>Match Details</h1>
                        <p>Unable to load this match.</p>
                    </div>
                </div>

                <div className="empty-state">
                    <h2>Match not found</h2>
                    <p>{error || "No match data available."}</p>

                    <Link
                        to="/matches"
                        className="primary-button"
                    >
                        ← Back to Matches
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="page-container">

            {/* =====================================================
                BACK LINK
            ====================================================== */}

            <Link
                to="/matches"
                className="back-link"
            >
                ← Back to Matches
            </Link>


            {/* =====================================================
                MATCH HEADER
            ====================================================== */}

            <div className="match-details-header">

                <div className="match-details-meta">

                    <span className="match-competition">
                        {match.competitionName ||
                            "Cricket Match"}
                    </span>

                    {match.competitionFormat && (
                        <span className="match-format">
                            {match.competitionFormat}
                        </span>
                    )}

                    {match.seasonName && (
                        <span className="match-format">
                            {match.seasonName}
                        </span>
                    )}

                    {match.stage && (
                        <span className="match-format">
                            {match.stage}
                        </span>
                    )}

                </div>


                <h1>
                    {team1?.teamName || "Team 1"}
                    <span className="match-title-vs">
                        {" "}vs{" "}
                    </span>
                    {team2?.teamName || "Team 2"}
                </h1>


                <p className="match-details-date">
                    {formatDate(match.matchDate)}
                </p>


                <div className="match-details-status">

                    <span
                        className={`match-status ${
                            match.matchStatus === "COMPLETED"
                                ? "completed"
                                : ""
                        }`}
                    >
                        {match.matchStatus}
                    </span>

                </div>

            </div>


            {/* =====================================================
                RESULT
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>Match Result</h2>
                        <p>
                            Official result and match outcome.
                        </p>
                    </div>
                </div>


                <div className="match-result-card">

                    <div className="match-result-team">

                        <div className="match-result-badge">
                            {team1?.teamShortName ||
                                team1?.teamName
                                    ?.substring(0, 3)
                                    .toUpperCase()}
                        </div>

                        <h3>
                            {team1?.teamName}
                        </h3>

                        <div className="match-result-score">
                            {team1?.runs ?? 0}/
                            {team1?.wickets ?? 0}
                        </div>

                        <span>
                            {team1?.overs || "0.0"} overs
                        </span>

                    </div>


                    <div className="match-result-center">

                        <span className="match-result-vs">
                            VS
                        </span>

                        {match.winner && (
                            <strong className="match-result-winner">
                                {match.winner} won
                            </strong>
                        )}

                    </div>


                    <div className="match-result-team">

                        <div className="match-result-badge">
                            {team2?.teamShortName ||
                                team2?.teamName
                                    ?.substring(0, 3)
                                    .toUpperCase()}
                        </div>

                        <h3>
                            {team2?.teamName}
                        </h3>

                        <div className="match-result-score">
                            {team2?.runs ?? 0}/
                            {team2?.wickets ?? 0}
                        </div>

                        <span>
                            {team2?.overs || "0.0"} overs
                        </span>

                    </div>

                </div>


                {match.resultDescription && (
                    <div className="match-result-description">
                        {match.resultDescription}
                    </div>
                )}

            </section>


            {/* =====================================================
                MATCH INFORMATION
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>Match Information</h2>
                        <p>Key details from the match.</p>
                    </div>
                </div>


                <div className="info-grid">

                    <div className="info-card">
                        <span>Venue</span>
                        <strong>
                            {match.venueName ||
                                "Unavailable"}
                        </strong>

                        {(match.venueCity ||
                            match.venueCountry) && (
                            <small>
                                {match.venueCity || ""}
                                {match.venueCity &&
                                    match.venueCountry
                                    ? ", "
                                    : ""}
                                {match.venueCountry || ""}
                            </small>
                        )}
                    </div>


                    <div className="info-card">
                        <span>Toss Winner</span>
                        <strong>
                            {match.tossWinner ||
                                "Unavailable"}
                        </strong>
                    </div>


                    <div className="info-card">
                        <span>Toss Decision</span>
                        <strong>
                            {match.tossDecision ||
                                "Unavailable"}
                        </strong>
                    </div>


                    <div className="info-card">
                        <span>Stage</span>
                        <strong>
                            {match.stage || "League"}
                        </strong>
                    </div>

                </div>

            </section>


            {/* =====================================================
                TEAM STATISTICS
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>Team Statistics</h2>
                        <p>
                            Batting output and scoring metrics.
                        </p>
                    </div>
                </div>


                <div className="stats-grid">

                    <div className="stat-card">
                        <span>
                            {team1?.teamShortName ||
                                team1?.teamName}
                        </span>
                        <strong>
                            {formatNumber(team1?.runs)}
                        </strong>
                        <small>Runs</small>
                    </div>


                    <div className="stat-card">
                        <span>
                            {team2?.teamShortName ||
                                team2?.teamName}
                        </span>
                        <strong>
                            {formatNumber(team2?.runs)}
                        </strong>
                        <small>Runs</small>
                    </div>


                    <div className="stat-card">
                        <span>Team 1 Run Rate</span>
                        <strong>
                            {formatDecimal(
                                team1?.runRate
                            )}
                        </strong>
                    </div>


                    <div className="stat-card">
                        <span>Team 2 Run Rate</span>
                        <strong>
                            {formatDecimal(
                                team2?.runRate
                            )}
                        </strong>
                    </div>


                    <div className="stat-card">
                        <span>Team 1 Fours</span>
                        <strong>
                            {formatNumber(team1?.fours)}
                        </strong>
                    </div>


                    <div className="stat-card">
                        <span>Team 2 Fours</span>
                        <strong>
                            {formatNumber(team2?.fours)}
                        </strong>
                    </div>


                    <div className="stat-card">
                        <span>Team 1 Sixes</span>
                        <strong>
                            {formatNumber(team1?.sixes)}
                        </strong>
                    </div>


                    <div className="stat-card">
                        <span>Team 2 Sixes</span>
                        <strong>
                            {formatNumber(team2?.sixes)}
                        </strong>
                    </div>

                </div>

            </section>


            {/* =====================================================
                TEAM 1 BATTING
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>
                            {team1?.teamName} Batting
                        </h2>
                        <p>
                            Individual batting performances.
                        </p>
                    </div>
                </div>

                {renderBattingTable(team1Players)}

            </section>


            {/* =====================================================
                TEAM 1 BOWLING
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>
                            {team1?.teamName} Bowling
                        </h2>
                        <p>
                            Individual bowling performances.
                        </p>
                    </div>
                </div>

                {renderBowlingTable(team1Players)}

            </section>


            {/* =====================================================
                TEAM 2 BATTING
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>
                            {team2?.teamName} Batting
                        </h2>
                        <p>
                            Individual batting performances.
                        </p>
                    </div>
                </div>

                {renderBattingTable(team2Players)}

            </section>


            {/* =====================================================
                TEAM 2 BOWLING
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>
                            {team2?.teamName} Bowling
                        </h2>
                        <p>
                            Individual bowling performances.
                        </p>
                    </div>
                </div>

                {renderBowlingTable(team2Players)}

            </section>


            {/* =====================================================
                EXPLORE MORE
            ====================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>Explore More</h2>
                        <p>
                            Continue exploring the cricket
                            analytics platform.
                        </p>
                    </div>
                </div>


                <div className="action-grid">

                    <Link
                        to="/matches"
                        className="action-card"
                    >
                        <h3>All Matches</h3>
                        <p>
                            Explore the complete match database.
                        </p>
                    </Link>


                    {team1?.teamId && (
                        <Link
                            to={`/teams/${team1.teamId}`}
                            className="action-card"
                        >
                            <h3>
                                {team1.teamName}
                            </h3>
                            <p>
                                View team analytics and
                                performance.
                            </p>
                        </Link>
                    )}


                    {team2?.teamId && (
                        <Link
                            to={`/teams/${team2.teamId}`}
                            className="action-card"
                        >
                            <h3>
                                {team2.teamName}
                            </h3>
                            <p>
                                View team analytics and
                                performance.
                            </p>
                        </Link>
                    )}


                    <Link
                        to="/leaderboards"
                        className="action-card"
                    >
                        <h3>Leaderboards</h3>
                        <p>
                            See the best players and teams.
                        </p>
                    </Link>

                </div>

            </section>

        </div>
    );
}

export default MatchDetails;