import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";
import api from "../services/api";

function MatchAnalytics() {

    const { matchId } = useParams();

    const [match, setMatch] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {

        const fetchMatchAnalytics = async () => {

            try {

                setLoading(true);
                setError("");

                const response = await api.get(
                    `/analytics/matches/${matchId}`
                );

                setMatch(response.data);

            } catch (err) {

                console.error(err);

                setError(
                    "Unable to load match analytics."
                );

            } finally {

                setLoading(false);

            }
        };

        fetchMatchAnalytics();

    }, [matchId]);

    if (loading) {

        return (
            <div className="page-container">

                <div className="status-message">
                    Loading match analytics...
                </div>

            </div>
        );
    }

    if (error) {

        return (
            <div className="page-container">

                <div className="status-message error">
                    {error}
                </div>

            </div>
        );
    }

    if (!match) {

        return (
            <div className="page-container">

                <div className="status-message">
                    Match analytics not found.
                </div>

            </div>
        );
    }

    const {
        competitionName,
        competitionFormat,
        matchDate,
        matchStatus,
        resultDescription,
        seasonName,
        team1,
        team2,
        tossDecision,
        tossWinner,
        venueName,
        venueCity,
        venueCountry,
        winner,
        playerPerformances,
    } = match;

    /*
     * Team score comparison
     */
    const scoreData = [
        {
            metric: "Runs",
            [team1.teamShortName]: team1.runs,
            [team2.teamShortName]: team2.runs,
        },
        {
            metric: "Fours",
            [team1.teamShortName]: team1.fours,
            [team2.teamShortName]: team2.fours,
        },
        {
            metric: "Sixes",
            [team1.teamShortName]: team1.sixes,
            [team2.teamShortName]: team2.sixes,
        },
        {
            metric: "Wickets",
            [team1.teamShortName]: team1.wickets,
            [team2.teamShortName]: team2.wickets,
        },
    ];

    /*
     * Player batting performances
     */
    const battingPerformances =
        playerPerformances.filter(
            (player) => player.ballsFaced > 0
        );

    /*
     * Format date for display
     */
    const formattedDate = new Date(
        `${matchDate}T00:00:00`
    ).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "long",
        year: "numeric",
    });

    return (
        <div className="page-container">

            {/* =====================================
                BACK LINK
            ====================================== */}

            <Link
                to="/matches"
                className="back-link"
            >
                ← Back to Matches
            </Link>


            {/* =====================================
                MATCH HEADER
            ====================================== */}

            <section className="match-analytics-header">

                <div className="match-header-top">

                    <div>

                        <span className="page-eyebrow">
                            MATCH ANALYTICS
                        </span>

                        <h1>
                            {team1.teamName}
                            {" "}
                            vs
                            {" "}
                            {team2.teamName}
                        </h1>

                        <p>
                            {competitionName}
                            {" • "}
                            {competitionFormat}
                            {" • "}
                            {seasonName}
                        </p>

                    </div>

                    <span
                        className={
                            matchStatus === "COMPLETED"
                                ? "match-status completed"
                                : "match-status"
                        }
                    >
                        {matchStatus}
                    </span>

                </div>


                {/* Match Score */}

                <div className="match-scoreboard">

                    <div
                        className={
                            winner === team1.teamName
                                ? "match-team-score winner"
                                : "match-team-score"
                        }
                    >

                        <span className="match-team-short">
                            {team1.teamShortName}
                        </span>

                        <h2>
                            {team1.runs}/{team1.wickets}
                        </h2>

                        <p>
                            {team1.overs} overs
                        </p>

                        <span>
                            RR {team1.runRate}
                        </span>

                    </div>


                    <div className="match-score-vs">
                        VS
                    </div>


                    <div
                        className={
                            winner === team2.teamName
                                ? "match-team-score winner"
                                : "match-team-score"
                        }
                    >

                        <span className="match-team-short">
                            {team2.teamShortName}
                        </span>

                        <h2>
                            {team2.runs}/{team2.wickets}
                        </h2>

                        <p>
                            {team2.overs} overs
                        </p>

                        <span>
                            RR {team2.runRate}
                        </span>

                    </div>

                </div>


                {/* Result */}

                <div className="match-result-banner">

                    <span>
                        RESULT
                    </span>

                    <strong>
                        {resultDescription}
                    </strong>

                </div>

            </section>


            {/* =====================================
                MATCH INFORMATION
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Match Information
                        </h2>

                        <p>
                            Match conditions and venue
                            information
                        </p>

                    </div>

                </div>


                <div className="match-info-grid">

                    <div className="match-info-card">

                        <span>
                            Date
                        </span>

                        <strong>
                            {formattedDate}
                        </strong>

                    </div>


                    <div className="match-info-card">

                        <span>
                            Competition
                        </span>

                        <strong>
                            {competitionName}
                        </strong>

                    </div>


                    <div className="match-info-card">

                        <span>
                            Venue
                        </span>

                        <strong>
                            {venueName}
                        </strong>

                        <small>
                            {venueCity}, {venueCountry}
                        </small>

                    </div>


                    <div className="match-info-card">

                        <span>
                            Toss Winner
                        </span>

                        <strong>
                            {tossWinner}
                        </strong>

                        <small>
                            Chose to {tossDecision.toLowerCase()}
                        </small>

                    </div>

                </div>

            </section>


            {/* =====================================
                TEAM SCORECARD
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Team Scorecard
                        </h2>

                        <p>
                            Overall batting performance
                            by team
                        </p>

                    </div>

                </div>


                <div className="team-scorecard-grid">

                    <div
                        className={
                            winner === team1.teamName
                                ? "scorecard-team-card winner"
                                : "scorecard-team-card"
                        }
                    >

                        <div className="scorecard-team-heading">

                            <div>

                                <span>
                                    {team1.teamShortName}
                                </span>

                                <h3>
                                    {team1.teamName}
                                </h3>

                            </div>

                            {winner === team1.teamName && (
                                <span className="winner-badge">
                                    WINNER
                                </span>
                            )}

                        </div>


                        <div className="scorecard-main-score">

                            <strong>
                                {team1.runs}/{team1.wickets}
                            </strong>

                            <span>
                                {team1.overs} overs
                            </span>

                        </div>


                        <div className="scorecard-stat-grid">

                            <div>
                                <span>Run Rate</span>
                                <strong>
                                    {team1.runRate}
                                </strong>
                            </div>

                            <div>
                                <span>4s</span>
                                <strong>
                                    {team1.fours}
                                </strong>
                            </div>

                            <div>
                                <span>6s</span>
                                <strong>
                                    {team1.sixes}
                                </strong>
                            </div>

                            <div>
                                <span>Extras</span>
                                <strong>
                                    {team1.extras}
                                </strong>
                            </div>

                            <div>
                                <span>Balls</span>
                                <strong>
                                    {team1.totalBalls}
                                </strong>
                            </div>

                        </div>

                    </div>


                    <div
                        className={
                            winner === team2.teamName
                                ? "scorecard-team-card winner"
                                : "scorecard-team-card"
                        }
                    >

                        <div className="scorecard-team-heading">

                            <div>

                                <span>
                                    {team2.teamShortName}
                                </span>

                                <h3>
                                    {team2.teamName}
                                </h3>

                            </div>

                            {winner === team2.teamName && (
                                <span className="winner-badge">
                                    WINNER
                                </span>
                            )}

                        </div>


                        <div className="scorecard-main-score">

                            <strong>
                                {team2.runs}/{team2.wickets}
                            </strong>

                            <span>
                                {team2.overs} overs
                            </span>

                        </div>


                        <div className="scorecard-stat-grid">

                            <div>
                                <span>Run Rate</span>
                                <strong>
                                    {team2.runRate}
                                </strong>
                            </div>

                            <div>
                                <span>4s</span>
                                <strong>
                                    {team2.fours}
                                </strong>
                            </div>

                            <div>
                                <span>6s</span>
                                <strong>
                                    {team2.sixes}
                                </strong>
                            </div>

                            <div>
                                <span>Extras</span>
                                <strong>
                                    {team2.extras}
                                </strong>
                            </div>

                            <div>
                                <span>Balls</span>
                                <strong>
                                    {team2.totalBalls}
                                </strong>
                            </div>

                        </div>

                    </div>

                </div>

            </section>


            {/* =====================================
                TEAM COMPARISON CHART
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Team Comparison
                        </h2>

                        <p>
                            Runs, boundaries and wickets
                        </p>

                    </div>

                </div>


                <div className="match-chart-card">

                    <ResponsiveContainer
                        width="100%"
                        height={400}
                    >

                        <BarChart
                            data={scoreData}
                            margin={{
                                top: 20,
                                right: 30,
                                left: 10,
                                bottom: 20,
                            }}
                            barGap={12}
                        >

                            <CartesianGrid
                                strokeDasharray="3 3"
                            />

                            <XAxis
                                dataKey="metric"
                            />

                            <YAxis />

                            <Tooltip />

                            <Legend />

                            <Bar
                                dataKey={
                                    team1.teamShortName
                                }
                                name={
                                    team1.teamName
                                }
                                fill="#2563eb"
                                radius={[
                                    6,
                                    6,
                                    0,
                                    0,
                                ]}
                            />

                            <Bar
                                dataKey={
                                    team2.teamShortName
                                }
                                name={
                                    team2.teamName
                                }
                                fill="#f59e0b"
                                radius={[
                                    6,
                                    6,
                                    0,
                                    0,
                                ]}
                            />

                        </BarChart>

                    </ResponsiveContainer>

                </div>

            </section>


            {/* =====================================
                PLAYER PERFORMANCE
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Player Performance
                        </h2>

                        <p>
                            Batting performances recorded
                            for this match
                        </p>

                    </div>

                </div>


                {battingPerformances.length > 0 ? (

                    <div className="match-player-grid">

                        {battingPerformances.map(
                            (player) => (

                                <Link
                                    key={player.playerId}
                                    to={`/players/${player.playerId}`}
                                    className="match-player-card"
                                >

                                    <div className="match-player-avatar">
                                        {player.playerName
                                            .charAt(0)
                                            .toUpperCase()}
                                    </div>


                                    <div className="match-player-info">

                                        <span className="comparison-role">
                                            {player.role}
                                        </span>

                                        <h3>
                                            {player.playerName}
                                        </h3>

                                        <p>
                                            {player.teamName}
                                        </p>

                                    </div>


                                    <div className="match-player-score">

                                        <strong>
                                            {player.battingRuns}
                                        </strong>

                                        <span>
                                            ({player.ballsFaced})
                                        </span>

                                    </div>


                                    <div className="match-player-metrics">

                                        <div>
                                            <span>SR</span>
                                            <strong>
                                                {
                                                    player.battingStrikeRate
                                                }
                                            </strong>
                                        </div>

                                        <div>
                                            <span>4s</span>
                                            <strong>
                                                {player.fours}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>6s</span>
                                            <strong>
                                                {player.sixes}
                                            </strong>
                                        </div>

                                        <div>
                                            <span>Wkts</span>
                                            <strong>
                                                {player.wickets}
                                            </strong>
                                        </div>

                                    </div>

                                </Link>

                            )
                        )}

                    </div>

                ) : (

                    <div className="empty-state">
                        No player performance data
                        available.
                    </div>

                )}

            </section>


            {/* =====================================
                BATTING LEADER
            ====================================== */}

            {battingPerformances.length > 0 && (

                <section className="profile-section">

                    <div className="section-heading">

                        <div>

                            <h2>
                                Match Highlight
                            </h2>

                            <p>
                                Top batting performance in
                                this match
                            </p>

                        </div>

                    </div>


                    {(() => {

                        const topBatter =
                            [...battingPerformances]
                                .sort(
                                    (a, b) =>
                                        b.battingRuns -
                                        a.battingRuns
                                )[0];

                        return (

                            <div className="match-highlight-card">

                                <div className="match-highlight-avatar">
                                    {topBatter.playerName
                                        .charAt(0)
                                        .toUpperCase()}
                                </div>

                                <div>

                                    <span>
                                        TOP SCORER
                                    </span>

                                    <h3>
                                        {topBatter.playerName}
                                    </h3>

                                    <p>
                                        {topBatter.teamName}
                                    </p>

                                </div>

                                <div className="match-highlight-score">

                                    <strong>
                                        {topBatter.battingRuns}
                                    </strong>

                                    <span>
                                        runs
                                    </span>

                                </div>

                                <div className="match-highlight-details">

                                    <span>
                                        {topBatter.ballsFaced}
                                        {" "}
                                        balls
                                    </span>

                                    <span>
                                        SR{" "}
                                        {
                                            topBatter.battingStrikeRate
                                        }
                                    </span>

                                    <span>
                                        {
                                            topBatter.fours
                                        }{" "}
                                        fours
                                    </span>

                                    <span>
                                        {
                                            topBatter.sixes
                                        }{" "}
                                        sixes
                                    </span>

                                </div>

                            </div>

                        );

                    })()}

                </section>

            )}


            {/* =====================================
                FOOTER
            ====================================== */}

            <div className="comparison-footer">

                <Link
                    to="/matches"
                    className="comparison-link"
                >
                    View All Matches
                </Link>

                <Link
                    to={`/teams/${team1.teamId}`}
                    className="comparison-link"
                >
                    {team1.teamName} Analytics
                </Link>

                <Link
                    to={`/teams/${team2.teamId}`}
                    className="comparison-link"
                >
                    {team2.teamName} Analytics
                </Link>

            </div>

        </div>
    );
}

export default MatchAnalytics;