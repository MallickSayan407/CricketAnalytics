import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
} from "recharts";
import api from "../services/api";

function SeasonAnalytics() {
    const { seasonId } = useParams();

    const [analytics, setAnalytics] = useState(null);
    const [standings, setStandings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchSeasonAnalytics = async () => {
            try {
                setLoading(true);
                setError("");

                const [analyticsResponse, standingsResponse] =
                    await Promise.all([
                        api.get(`/analytics/seasons/${seasonId}`),
                        api.get(`/analytics/seasons/${seasonId}/standings`),
                    ]);

                setAnalytics(analyticsResponse.data);
                setStandings(standingsResponse.data || []);
            } catch (err) {
                console.error(err);
                setError(
                    err.response?.data?.message ||
                        "Failed to load season analytics."
                );
            } finally {
                setLoading(false);
            }
        };

        if (seasonId) {
            fetchSeasonAnalytics();
        }
    }, [seasonId]);

    if (loading) {
        return (
            <div className="page-container">
                <div className="loading-state">Loading season analytics...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container">
                <div className="error-state">{error}</div>
            </div>
        );
    }

    if (!analytics) {
        return (
            <div className="page-container">
                <div className="empty-state">
                    No season analytics available.
                </div>
            </div>
        );
    }

    const scoringData = [
        {
            name: "Runs",
            value: analytics.totalRuns || 0,
        },
        {
            name: "Fours",
            value: analytics.totalFours || 0,
        },
        {
            name: "Sixes",
            value: analytics.totalSixes || 0,
        },
    ];

    return (
        <div className="page-container">
            {/* HEADER */}
            <div className="page-header">
                <div>
                    <h1>{analytics.seasonName || "Season Analytics"}</h1>

                    <p>
                        {analytics.competitionName || "Competition"} ·{" "}
                        {analytics.seasonFormat || "Cricket"}
                    </p>
                </div>

                <Link to="/seasons" className="secondary-button">
                    ← Back to Seasons
                </Link>
            </div>

            {/* OVERVIEW */}
            <section className="stats-grid">
                <div className="stat-card">
                    <span className="stat-label">Matches</span>
                    <strong>{analytics.totalMatches || 0}</strong>
                </div>

                <div className="stat-card">
                    <span className="stat-label">Total Runs</span>
                    <strong>{analytics.totalRuns || 0}</strong>
                </div>

                <div className="stat-card">
                    <span className="stat-label">Fours</span>
                    <strong>{analytics.totalFours || 0}</strong>
                </div>

                <div className="stat-card">
                    <span className="stat-label">Sixes</span>
                    <strong>{analytics.totalSixes || 0}</strong>
                </div>
            </section>

            {/* SEASON INFORMATION */}
            <section className="content-section">
                <div className="section-header">
                    <h2>Season Information</h2>
                </div>

                <div className="info-grid">
                    <div className="info-item">
                        <span>Season</span>
                        <strong>
                            {analytics.seasonName || "-"}
                        </strong>
                    </div>

                    <div className="info-item">
                        <span>Competition</span>
                        <strong>
                            {analytics.competitionName || "-"}
                        </strong>
                    </div>

                    <div className="info-item">
                        <span>Format</span>
                        <strong>
                            {analytics.seasonFormat || "-"}
                        </strong>
                    </div>

                    <div className="info-item">
                        <span>Total Matches</span>
                        <strong>
                            {analytics.totalMatches || 0}
                        </strong>
                    </div>
                </div>
            </section>

            {/* TEAM STANDINGS */}
            <section className="content-section">
                <div className="section-header">
                    <div>
                        <h2>Team Standings</h2>
                        <p>League table and team performance</p>
                    </div>
                </div>

                {standings.length === 0 ? (
                    <div className="empty-state">
                        No standings available.
                    </div>
                ) : (
                    <div className="table-container">
                        <table className="data-table standings-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Team</th>
                                    <th>Mat</th>
                                    <th>Won</th>
                                    <th>Lost</th>
                                    <th>NR</th>
                                    <th>Pts</th>
                                    <th>Win %</th>
                                    <th>RR</th>
                                    <th>BR</th>
                                    <th>NRR</th>
                                </tr>
                            </thead>

                            <tbody>
                                {standings.map((team) => (
                                    <tr key={team.teamId}>
                                        <td>
                                            <strong>{team.rank}</strong>
                                        </td>

                                        <td>
                                            <Link
                                                to={`/teams/${team.teamId}`}
                                                className="table-link"
                                            >
                                                <strong>
                                                    {team.teamShortName ||
                                                        team.teamName}
                                                </strong>

                                                {team.teamShortName && (
                                                    <span className="table-secondary">
                                                        {team.teamName}
                                                    </span>
                                                )}
                                            </Link>
                                        </td>

                                        <td>{team.matches}</td>

                                        <td>{team.wins}</td>

                                        <td>{team.losses}</td>

                                        <td>{team.noResults}</td>

                                        <td>
                                            <strong>{team.points}</strong>
                                        </td>

                                        <td>
                                            {team.winPercentage != null
                                                ? `${team.winPercentage.toFixed(
                                                      2
                                                  )}%`
                                                : "-"}
                                        </td>

                                        <td>
                                            {team.runRate != null
                                                ? team.runRate.toFixed(2)
                                                : "-"}
                                        </td>

                                        <td>
                                            {team.bowlingRate != null
                                                ? team.bowlingRate.toFixed(2)
                                                : "-"}
                                        </td>

                                        <td>
                                            {team.netRunRate != null
                                                ? `${
                                                      team.netRunRate >= 0
                                                          ? "+"
                                                          : ""
                                                  }${team.netRunRate.toFixed(
                                                      3
                                                  )}`
                                                : "-"}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* MATCH RESULTS */}
            <section className="content-section">
                <div className="section-header">
                    <div>
                        <h2>Match Results</h2>
                        <p>Season result distribution</p>
                    </div>
                </div>

                <div className="info-grid">
                    <div className="info-item">
                        <span>Completed</span>
                        <strong>
                            {analytics.completedMatches || 0}
                        </strong>
                    </div>

                    <div className="info-item">
                        <span>No Results</span>
                        <strong>
                            {analytics.noResultMatches || 0}
                        </strong>
                    </div>

                    <div className="info-item">
                        <span>Ties</span>
                        <strong>{analytics.tiedMatches || 0}</strong>
                    </div>

                    <div className="info-item">
                        <span>Average Runs / Match</span>
                        <strong>
                            {analytics.totalMatches
                                ? (
                                      analytics.totalRuns /
                                      analytics.totalMatches
                                  ).toFixed(1)
                                : "0.0"}
                        </strong>
                    </div>
                </div>
            </section>

            {/* SCORING CHART */}
            <section className="content-section">
                <div className="section-header">
                    <div>
                        <h2>Scoring Overview</h2>
                        <p>Runs and boundary distribution</p>
                    </div>
                </div>

                <div className="chart-container">
                    <ResponsiveContainer width="100%" height={350}>
                        <BarChart data={scoringData}>
                            <CartesianGrid strokeDasharray="3 3" />

                            <XAxis dataKey="name" />

                            <YAxis />

                            <Tooltip />

                            <Legend />

                            <Bar
                                dataKey="value"
                                name="Count"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </section>

            {/* RUN STATISTICS */}
            <section className="content-section">
                <div className="section-header">
                    <h2>Run Statistics</h2>
                </div>

                <div className="stats-grid">
                    <div className="stat-card">
                        <span className="stat-label">
                            Total Runs
                        </span>
                        <strong>
                            {analytics.totalRuns || 0}
                        </strong>
                    </div>

                    <div className="stat-card">
                        <span className="stat-label">
                            Total Fours
                        </span>
                        <strong>
                            {analytics.totalFours || 0}
                        </strong>
                    </div>

                    <div className="stat-card">
                        <span className="stat-label">
                            Total Sixes
                        </span>
                        <strong>
                            {analytics.totalSixes || 0}
                        </strong>
                    </div>

                    <div className="stat-card">
                        <span className="stat-label">
                            Boundary Runs
                        </span>
                        <strong>
                            {(analytics.totalFours || 0) * 4 +
                                (analytics.totalSixes || 0) * 6}
                        </strong>
                    </div>
                </div>
            </section>

            {/* BOUNDARIES */}
            <section className="content-section">
                <div className="section-header">
                    <div>
                        <h2>Boundary Statistics</h2>
                        <p>Four and six distribution</p>
                    </div>
                </div>

                <div className="chart-container">
                    <ResponsiveContainer width="100%" height={320}>
                        <BarChart
                            data={[
                                {
                                    name: "Fours",
                                    value: analytics.totalFours || 0,
                                },
                                {
                                    name: "Sixes",
                                    value: analytics.totalSixes || 0,
                                },
                            ]}
                        >
                            <CartesianGrid strokeDasharray="3 3" />

                            <XAxis dataKey="name" />

                            <YAxis />

                            <Tooltip />

                            <Bar
                                dataKey="value"
                                name="Boundaries"
                            />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </section>
        </div>
    );
}

export default SeasonAnalytics;