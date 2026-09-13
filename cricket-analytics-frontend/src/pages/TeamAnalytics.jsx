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
    PieChart,
    Pie,
    Cell,
} from "recharts";
import api from "../services/api";

function TeamAnalytics() {

    const { teamId } = useParams();

    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {

        const fetchTeamAnalytics = async () => {

            try {

                setLoading(true);
                setError("");

                const response = await api.get(
                    `/analytics/teams/${teamId}`
                );

                setAnalytics(response.data);

            } catch (err) {

                console.error(err);

                setError(
                    "Unable to load team analytics."
                );

            } finally {

                setLoading(false);

            }
        };

        fetchTeamAnalytics();

    }, [teamId]);

    if (loading) {

        return (
            <div className="page-container">

                <div className="status-message">
                    Loading team analytics...
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

    if (!analytics) {

        return (
            <div className="page-container">

                <div className="status-message">
                    Team analytics not found.
                </div>

            </div>
        );
    }

    const {
        teamName,
        teamShortName,
        matchStats,
        performance,
    } = analytics;

    /*
     * Match result chart
     */
    const resultData = [
        {
            name: "Wins",
            value: matchStats.wins,
        },
        {
            name: "Losses",
            value: matchStats.losses,
        },
        {
            name: "Ties",
            value: matchStats.ties,
        },
        {
            name: "No Results",
            value: matchStats.noResults,
        },
    ];

    /*
     * Remove zero-result categories from the pie chart.
     */
    const visibleResultData = resultData.filter(
        (item) => item.value > 0
    );

    /*
     * Performance chart
     */
    const performanceData = [
        {
            metric: "Runs",
            value: performance.runsScored,
        },
        {
            metric: "4s",
            value: performance.fours,
        },
        {
            metric: "6s",
            value: performance.sixes,
        },
        {
            metric: "Wickets Lost",
            value: performance.wicketsLost,
        },
    ];

    return (
        <div className="page-container">

            {/* =====================================
                BACK LINK
            ====================================== */}

            <Link
                to="/teams"
                className="back-link"
            >
                ← Back to Teams
            </Link>


            {/* =====================================
                TEAM HEADER
            ====================================== */}

            <section className="team-analytics-header">

                <div className="team-analytics-badge">
                    {teamShortName}
                </div>

                <div>

                    <span className="page-eyebrow">
                        TEAM ANALYTICS
                    </span>

                    <h1>
                        {teamName}
                    </h1>

                    <p>
                        {teamShortName} • Performance
                        analytics
                    </p>

                </div>

            </section>


            {/* =====================================
                MATCH SUMMARY
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Match Summary
                        </h2>

                        <p>
                            Overall results across recorded
                            matches
                        </p>

                    </div>

                </div>


                <div className="team-stat-grid">

                    <div className="team-stat-card">

                        <span>
                            Matches
                        </span>

                        <strong>
                            {matchStats.matches}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Wins
                        </span>

                        <strong>
                            {matchStats.wins}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Losses
                        </span>

                        <strong>
                            {matchStats.losses}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Ties
                        </span>

                        <strong>
                            {matchStats.ties}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            No Results
                        </span>

                        <strong>
                            {matchStats.noResults}
                        </strong>

                    </div>


                    <div className="team-stat-card highlight">

                        <span>
                            Win Percentage
                        </span>

                        <strong>
                            {matchStats.winPercentage}%
                        </strong>

                    </div>

                </div>

            </section>


            {/* =====================================
                PERFORMANCE SUMMARY
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Batting Performance
                        </h2>

                        <p>
                            Team batting output from
                            recorded matches
                        </p>

                    </div>

                </div>


                <div className="team-stat-grid">

                    <div className="team-stat-card">

                        <span>
                            Runs Scored
                        </span>

                        <strong>
                            {performance.runsScored}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Average Runs
                        </span>

                        <strong>
                            {performance.averageRuns}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Average Run Rate
                        </span>

                        <strong>
                            {performance.averageRunRate}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Wickets Lost
                        </span>

                        <strong>
                            {performance.wicketsLost}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Fours
                        </span>

                        <strong>
                            {performance.fours}
                        </strong>

                    </div>


                    <div className="team-stat-card">

                        <span>
                            Sixes
                        </span>

                        <strong>
                            {performance.sixes}
                        </strong>

                    </div>

                </div>

            </section>


            {/* =====================================
                CHARTS
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Team Performance
                        </h2>

                        <p>
                            Visual breakdown of team
                            statistics
                        </p>

                    </div>

                </div>


                {/* =================================
                    BATTING OUTPUT
                ================================== */}

                <div className="team-chart-section">

                    <div className="team-chart-heading">

                        <h3>
                            Batting Output
                        </h3>

                        <p>
                            Runs, boundaries and wickets
                            lost
                        </p>

                    </div>


                    <div className="team-chart-card">

                        <ResponsiveContainer
                            width="100%"
                            height={400}
                        >

                            <BarChart
                                data={performanceData}
                                margin={{
                                    top: 20,
                                    right: 30,
                                    left: 10,
                                    bottom: 20,
                                }}
                            >

                                <CartesianGrid
                                    strokeDasharray="3 3"
                                />

                                <XAxis
                                    dataKey="metric"
                                />

                                <YAxis />

                                <Tooltip />

                                <Bar
                                    dataKey="value"
                                    name="Value"
                                    fill="#2563eb"
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

                </div>


                {/* =================================
                    MATCH RESULTS
                ================================== */}

                <div className="team-chart-section">

                    <div className="team-chart-heading">

                        <h3>
                            Match Results
                        </h3>

                        <p>
                            Distribution of wins,
                            losses and other results
                        </p>

                    </div>


                    <div className="team-chart-card team-result-chart">

                        {visibleResultData.length > 0 ? (

                            <ResponsiveContainer
                                width="100%"
                                height={400}
                            >

                                <PieChart>

                                    <Pie
                                        data={
                                            visibleResultData
                                        }
                                        dataKey="value"
                                        nameKey="name"
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={130}
                                        label
                                    >

                                        {visibleResultData.map(
                                            (entry, index) => (

                                                <Cell
                                                    key={
                                                        `cell-${index}`
                                                    }
                                                    fill={
                                                        [
                                                            "#2563eb",
                                                            "#ef4444",
                                                            "#f59e0b",
                                                            "#777777",
                                                        ][
                                                            index %
                                                                4
                                                        ]
                                                    }
                                                />

                                            )
                                        )}

                                    </Pie>

                                    <Tooltip />

                                    <Legend />

                                </PieChart>

                            </ResponsiveContainer>

                        ) : (

                            <div className="empty-state">

                                No match result data
                                available.

                            </div>

                        )}

                    </div>

                </div>

            </section>


            {/* =====================================
                KEY INSIGHTS
            ====================================== */}

            <section className="profile-section">

                <div className="section-heading">

                    <div>

                        <h2>
                            Key Insights
                        </h2>

                        <p>
                            Highlights from the available
                            team data
                        </p>

                    </div>

                </div>


                <div className="team-insights-grid">

                    <div className="team-insight-card">

                        <span>
                            Win Rate
                        </span>

                        <strong>
                            {matchStats.winPercentage}%
                        </strong>

                        <p>
                            Based on{" "}
                            {matchStats.matches}{" "}
                            recorded match
                            {matchStats.matches !== 1
                                ? "es"
                                : ""}
                        </p>

                    </div>


                    <div className="team-insight-card">

                        <span>
                            Scoring Rate
                        </span>

                        <strong>
                            {performance.averageRunRate}
                        </strong>

                        <p>
                            Average runs scored per
                            over
                        </p>

                    </div>


                    <div className="team-insight-card">

                        <span>
                            Boundary Count
                        </span>

                        <strong>
                            {performance.fours +
                                performance.sixes}
                        </strong>

                        <p>
                            Combined fours and sixes
                        </p>

                    </div>

                </div>

            </section>


            {/* =====================================
                FOOTER
            ====================================== */}

            <div className="comparison-footer">

                <Link
                    to="/teams"
                    className="comparison-link"
                >
                    View All Teams
                </Link>

            </div>

        </div>
    );
}

export default TeamAnalytics;