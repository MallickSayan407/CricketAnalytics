import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
} from "recharts";
import api from "../services/api";

function VenueAnalytics() {
    const { venueId } = useParams();

    const [analytics, setAnalytics] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchVenueAnalytics();
    }, [venueId]);

    const fetchVenueAnalytics = async () => {
        try {
            setLoading(true);
            setError("");

            const response = await api.get(
                `/analytics/venues/${venueId}`
            );

            setAnalytics(response.data);
        } catch (err) {
            console.error("Error fetching venue analytics:", err);
            setError("Unable to load venue analytics.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="page-container">
                <p>Loading venue analytics...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container">
                <h1>Venue Analytics</h1>
                <p className="error-message">{error}</p>

                <Link to="/venues" className="back-link">
                    ← Back to Venues
                </Link>
            </div>
        );
    }

    if (!analytics) {
        return null;
    }

    const scoreChartData = [
        {
            name: "Highest",
            score: analytics.highestTeamScore || 0,
        },
        {
            name: "Average",
            score: analytics.averageFirstInningsScore || 0,
        },
        {
            name: "Lowest",
            score: analytics.lowestTeamScore || 0,
        },
    ];

    const resultChartData = [
        {
            name: "Team 1 Wins",
            value: analytics.team1Wins || 0,
        },
        {
            name: "Team 2 Wins",
            value: analytics.team2Wins || 0,
        },
        {
            name: "Ties",
            value: analytics.tiedMatches || 0,
        },
        {
            name: "No Results",
            value: analytics.noResultMatches || 0,
        },
    ];

    return (
        <div className="page-container venue-analytics-page">

            <Link to="/venues" className="back-link">
                ← Back to Venues
            </Link>

            <div className="venue-analytics-header">

                <div>
                    <span className="analytics-label">
                        VENUE ANALYTICS
                    </span>

                    <h1>{analytics.venueName}</h1>

                    <p>
                        {analytics.city}
                        {analytics.country &&
                            `, ${analytics.country}`}
                    </p>
                </div>

                <div className="venue-header-icon">
                    🏟️
                </div>

            </div>

            {/* Overview Cards */}

            <div className="analytics-stat-grid">

                <div className="analytics-stat-card">
                    <span>Total Matches</span>
                    <strong>
                        {analytics.totalMatches}
                    </strong>
                    <small>
                        Matches played at this venue
                    </small>
                </div>

                <div className="analytics-stat-card">
                    <span>Average Score</span>
                    <strong>
                        {analytics.averageFirstInningsScore?.toFixed(0)}
                    </strong>
                    <small>
                        First innings average
                    </small>
                </div>

                <div className="analytics-stat-card">
                    <span>Average Run Rate</span>
                    <strong>
                        {analytics.averageRunRate?.toFixed(2)}
                    </strong>
                    <small>
                        Overall scoring rate
                    </small>
                </div>

                <div className="analytics-stat-card">
                    <span>Capacity</span>
                    <strong>
                        {analytics.capacity
                            ? analytics.capacity.toLocaleString()
                            : "—"}
                    </strong>
                    <small>
                        Stadium capacity
                    </small>
                </div>

            </div>

            {/* Score Summary */}

            <div className="analytics-section">

                <div className="analytics-section-header">
                    <div>
                        <h2>Scoring Overview</h2>
                        <p>
                            Score characteristics at {analytics.venueName}.
                        </p>
                    </div>
                </div>

                <div className="analytics-chart-card">

                    <ResponsiveContainer
                        width="100%"
                        height={320}
                    >
                        <BarChart data={scoreChartData}>

                            <CartesianGrid strokeDasharray="3 3" />

                            <XAxis dataKey="name" />

                            <YAxis />

                            <Tooltip />

                            <Bar
                                dataKey="score"
                                name="Runs"
                                fill="#2563eb"
                                radius={[6, 6, 0, 0]}
                            />

                        </BarChart>
                    </ResponsiveContainer>

                </div>

            </div>

            {/* Score Statistics */}

            <div className="analytics-card-grid">

                <div className="analytics-info-card">

                    <h3>Match Scoring</h3>

                    <div className="analytics-row">
                        <span>Average first innings</span>
                        <strong>
                            {analytics.averageFirstInningsScore?.toFixed(0)}
                        </strong>
                    </div>

                    <div className="analytics-row">
                        <span>Average second innings</span>
                        <strong>
                            {analytics.averageSecondInningsScore?.toFixed(0)}
                        </strong>
                    </div>

                    <div className="analytics-row">
                        <span>Average match runs</span>
                        <strong>
                            {analytics.averageMatchRuns?.toFixed(0)}
                        </strong>
                    </div>

                    <div className="analytics-row">
                        <span>Average run rate</span>
                        <strong>
                            {analytics.averageRunRate?.toFixed(2)}
                        </strong>
                    </div>

                </div>

                <div className="analytics-info-card">

                    <h3>Score Records</h3>

                    <div className="analytics-row">
                        <span>Highest team score</span>
                        <strong>
                            {analytics.highestTeamScore}
                        </strong>
                    </div>

                    <div className="analytics-row">
                        <span>Lowest team score</span>
                        <strong>
                            {analytics.lowestTeamScore}
                        </strong>
                    </div>

                    <div className="analytics-row">
                        <span>Total fours</span>
                        <strong>
                            {analytics.totalFours}
                        </strong>
                    </div>

                    <div className="analytics-row">
                        <span>Total sixes</span>
                        <strong>
                            {analytics.totalSixes}
                        </strong>
                    </div>

                </div>

            </div>

            {/* Match Results */}

            <div className="analytics-section">

                <div className="analytics-section-header">
                    <div>
                        <h2>Match Results</h2>
                        <p>
                            Results recorded at this venue.
                        </p>
                    </div>
                </div>

                <div className="analytics-card-grid">

                    <div className="analytics-info-card">

                        <h3>Results Summary</h3>

                        <div className="analytics-row">
                            <span>Team 1 wins</span>
                            <strong>
                                {analytics.team1Wins}
                            </strong>
                        </div>

                        <div className="analytics-row">
                            <span>Team 2 wins</span>
                            <strong>
                                {analytics.team2Wins}
                            </strong>
                        </div>

                        <div className="analytics-row">
                            <span>Tied matches</span>
                            <strong>
                                {analytics.tiedMatches}
                            </strong>
                        </div>

                        <div className="analytics-row">
                            <span>No results</span>
                            <strong>
                                {analytics.noResultMatches}
                            </strong>
                        </div>

                    </div>

                    <div className="analytics-chart-card">

                        <ResponsiveContainer
                            width="100%"
                            height={280}
                        >
                            <BarChart data={resultChartData}>

                                <CartesianGrid strokeDasharray="3 3" />

                                <XAxis dataKey="name" />

                                <YAxis allowDecimals={false} />

                                <Tooltip />

                                <Bar
                                    dataKey="value"
                                    name="Matches"
                                    fill="#16a34a"
                                    radius={[6, 6, 0, 0]}
                                />

                            </BarChart>
                        </ResponsiveContainer>

                    </div>

                </div>

            </div>

            {/* Key Insights */}

            <div className="analytics-section">

                <div className="analytics-section-header">
                    <div>
                        <h2>Key Insights</h2>
                        <p>
                            Important characteristics of this venue.
                        </p>
                    </div>
                </div>

                <div className="insight-grid">

                    <div className="insight-card">
                        <span className="insight-icon">📊</span>
                        <div>
                            <h3>Scoring Environment</h3>
                            <p>
                                Matches at this venue have an average
                                first-innings score of{" "}
                                <strong>
                                    {analytics.averageFirstInningsScore?.toFixed(
                                        0
                                    )}
                                </strong>{" "}
                                runs.
                            </p>
                        </div>
                    </div>

                    <div className="insight-card">
                        <span className="insight-icon">⚡</span>
                        <div>
                            <h3>Run Rate</h3>
                            <p>
                                The average scoring rate is{" "}
                                <strong>
                                    {analytics.averageRunRate?.toFixed(2)}
                                </strong>{" "}
                                runs per over.
                            </p>
                        </div>
                    </div>

                    <div className="insight-card">
                        <span className="insight-icon">🏏</span>
                        <div>
                            <h3>Boundary Count</h3>
                            <p>
                                Recorded matches contain{" "}
                                <strong>
                                    {(analytics.totalFours || 0) +
                                        (analytics.totalSixes || 0)}
                                </strong>{" "}
                                fours and sixes combined.
                            </p>
                        </div>
                    </div>

                </div>

            </div>

        </div>
    );
}

export default VenueAnalytics;