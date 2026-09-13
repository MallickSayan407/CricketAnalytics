import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import api from "../services/api";
import "./TeamProfile.css";

function round(value, digits = 2) {
    const number = Number(value);
    if (!Number.isFinite(number)) return 0;
    return Number(number.toFixed(digits));
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function TeamProfile() {
    const { teamId } = useParams();

    const [baseAnalytics, setBaseAnalytics] = useState(null);
    const [competitions, setCompetitions] = useState([]);
    const [seasons, setSeasons] = useState([]);

    const [selectedCompetition, setSelectedCompetition] =
        useState("overall");
    const [selectedSeason, setSelectedSeason] =
        useState("overall");

    const [analytics, setAnalytics] = useState(null);
    const [trendData, setTrendData] = useState([]);

    const [loading, setLoading] = useState(true);
    const [analyticsLoading, setAnalyticsLoading] =
        useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        const loadFilters = async () => {
            try {
                const [competitionResponse, seasonResponse] =
                    await Promise.all([
                        api.get("/competitions"),
                        api.get("/seasons"),
                    ]);

                setCompetitions(
                    Array.isArray(competitionResponse.data)
                        ? competitionResponse.data
                        : []
                );

                setSeasons(
                    Array.isArray(seasonResponse.data)
                        ? seasonResponse.data
                        : []
                );
            } catch (err) {
                console.error(
                    "Failed to load team profile filters:",
                    err
                );
            }
        };

        loadFilters();
    }, []);

    useEffect(() => {
        const loadBaseAnalytics = async () => {
            try {
                setLoading(true);
                setError("");

                const response = await api.get(
                    `/analytics/teams/${teamId}`
                );

                setBaseAnalytics(response.data);
                setAnalytics(response.data);
            } catch (err) {
                console.error(
                    "Failed to load team analytics:",
                    err
                );

                setError(
                    err.response?.data?.message ||
                        "Unable to load team profile."
                );
            } finally {
                setLoading(false);
            }
        };

        if (teamId) {
            loadBaseAnalytics();
        }
    }, [teamId]);

    const filteredSeasons = useMemo(() => {
        if (selectedCompetition === "overall") {
            return [];
        }

        return seasons.filter(
            (season) =>
                String(season.competitionId) ===
                String(selectedCompetition)
        );
    }, [seasons, selectedCompetition]);

    const loadStandingsForSeason = async (seasonId) => {
        const response = await api.get(
            `/analytics/seasons/${seasonId}/standings`
        );

        return Array.isArray(response.data)
            ? response.data
            : [];
    };

    const buildCompetitionAnalytics = (rows) => {
        const teamRows = rows.filter(
            (row) =>
                String(row.teamId) === String(teamId)
        );

        if (teamRows.length === 0) {
            return null;
        }

        const total = teamRows.reduce(
            (acc, row) => ({
                matches:
                    acc.matches + Number(row.matches || 0),
                wins:
                    acc.wins + Number(row.wins || 0),
                losses:
                    acc.losses + Number(row.losses || 0),
                ties:
                    acc.ties + Number(row.ties || 0),
                noResults:
                    acc.noResults +
                    Number(row.noResults || 0),
                points:
                    acc.points + Number(row.points || 0),
                runsScored:
                    acc.runsScored +
                    Number(row.runsScored || 0),
                ballsFaced:
                    acc.ballsFaced +
                    Number(row.ballsFaced || 0),
                runsConceded:
                    acc.runsConceded +
                    Number(row.runsConceded || 0),
                ballsBowled:
                    acc.ballsBowled +
                    Number(row.ballsBowled || 0),
            }),
            {
                matches: 0,
                wins: 0,
                losses: 0,
                ties: 0,
                noResults: 0,
                points: 0,
                runsScored: 0,
                ballsFaced: 0,
                runsConceded: 0,
                ballsBowled: 0,
            }
        );

        const averageRuns =
            total.matches > 0
                ? total.runsScored / total.matches
                : 0;

        const runRate =
            total.ballsFaced > 0
                ? total.runsScored /
                  (total.ballsFaced / 6)
                : 0;

        const bowlingRate =
            total.ballsBowled > 0
                ? total.runsConceded /
                  (total.ballsBowled / 6)
                : 0;

        return {
            teamName: teamRows[0].teamName,
            teamShortName: teamRows[0].teamShortName,
            matchStats: {
                matches: total.matches,
                wins: total.wins,
                losses: total.losses,
                ties: total.ties,
                noResults: total.noResults,
                points: total.points,
                winPercentage:
                    total.matches > 0
                        ? round(
                              (total.wins /
                                  total.matches) *
                                  100
                          )
                        : 0,
            },
            performance: {
                runsScored: total.runsScored,
                averageRuns: round(averageRuns),
                averageRunRate: round(runRate),
                runsConceded:
                    total.runsConceded,
                bowlingRate: round(bowlingRate),
                netRunRate: round(
                    runRate - bowlingRate
                ),
            },
        };
    };

    useEffect(() => {
        const loadFilteredAnalytics = async () => {
            if (!baseAnalytics) {
                return;
            }

            if (selectedCompetition === "overall") {
                setAnalytics(baseAnalytics);
                setTrendData([]);
                setAnalyticsLoading(false);
                return;
            }

            try {
                setAnalyticsLoading(true);
                setError("");

                if (selectedSeason !== "overall") {
                    const rows =
                        await loadStandingsForSeason(
                            selectedSeason
                        );

                    const teamRow = rows.find(
                        (row) =>
                            String(row.teamId) ===
                            String(teamId)
                    );

                    if (!teamRow) {
                        setAnalytics(null);
                        setTrendData([]);
                        return;
                    }

                    setAnalytics({
                        teamName: teamRow.teamName,
                        teamShortName:
                            teamRow.teamShortName,
                        matchStats: {
                            matches:
                                teamRow.matches || 0,
                            wins:
                                teamRow.wins || 0,
                            losses:
                                teamRow.losses || 0,
                            ties:
                                teamRow.ties || 0,
                            noResults:
                                teamRow.noResults || 0,
                            points:
                                teamRow.points || 0,
                            winPercentage:
                                teamRow.winPercentage || 0,
                        },
                        performance: {
                            runsScored:
                                teamRow.runsScored || 0,
                            averageRuns:
                                teamRow.matches > 0
                                    ? round(
                                          teamRow.runsScored /
                                              teamRow.matches
                                      )
                                    : 0,
                            averageRunRate:
                                teamRow.runRate || 0,
                            runsConceded:
                                teamRow.runsConceded || 0,
                            bowlingRate:
                                teamRow.bowlingRate || 0,
                            netRunRate:
                                teamRow.netRunRate || 0,
                        },
                    });

                    setTrendData([teamRow]);
                    return;
                }

                const responses = await Promise.all(
                    filteredSeasons.map((season) =>
                        loadStandingsForSeason(
                            season.id
                        )
                    )
                );

                const allRows = responses.flat();

                setAnalytics(
                    buildCompetitionAnalytics(
                        allRows
                    )
                );

                const teamTrend = allRows
                    .filter(
                        (row) =>
                            String(row.teamId) ===
                            String(teamId)
                    )
                    .sort((a, b) =>
                        String(a.seasonName).localeCompare(
                            String(b.seasonName),
                            undefined,
                            { numeric: true }
                        )
                    );

                setTrendData(teamTrend);
            } catch (err) {
                console.error(
                    "Failed to load filtered team analytics:",
                    err
                );

                setAnalytics(null);

                setError(
                    err.response?.data?.message ||
                        "Unable to load selected team data."
                );
            } finally {
                setAnalyticsLoading(false);
            }
        };

        loadFilteredAnalytics();
    }, [
        baseAnalytics,
        filteredSeasons,
        selectedCompetition,
        selectedSeason,
        teamId,
    ]);

    const handleCompetitionChange = (event) => {
        setSelectedCompetition(
            event.target.value
        );
        setSelectedSeason("overall");
        setError("");
    };

    const handleSeasonChange = (event) => {
        setSelectedSeason(
            event.target.value
        );
        setError("");
    };

    if (loading) {
        return (
            <div className="page-container">
                <div className="status-message">
                    Loading team profile...
                </div>
            </div>
        );
    }

    if (error && !analytics) {
        return (
            <div className="page-container">
                <Link
                    to="/teams"
                    className="back-link"
                >
                    ← Back to Teams
                </Link>

                <div className="status-message error">
                    {error}
                </div>
            </div>
        );
    }

    if (!analytics) {
        return (
            <div className="page-container">
                <Link
                    to="/teams"
                    className="back-link"
                >
                    ← Back to Teams
                </Link>

                <div className="status-message">
                    No team data is available for the
                    selected filter.
                </div>
            </div>
        );
    }

    const {
        teamName,
        teamShortName,
        matchStats = {},
        performance = {},
    } = analytics;

    const resultData = [
        {
            name: "Wins",
            value: Number(
                matchStats.wins || 0
            ),
        },
        {
            name: "Losses",
            value: Number(
                matchStats.losses || 0
            ),
        },
        {
            name: "Ties",
            value: Number(
                matchStats.ties || 0
            ),
        },
        {
            name: "No Results",
            value: Number(
                matchStats.noResults || 0
            ),
        },
    ].filter((item) => item.value > 0);

    const performanceData = [
        {
            metric: "Runs",
            value: Number(
                performance.runsScored || 0
            ),
        },
        {
            metric: "Runs Conceded",
            value: Number(
                performance.runsConceded || 0
            ),
        },
        {
            metric: "Run Rate",
            value: Number(
                performance.averageRunRate || 0
            ),
        },
        {
            metric: "Net Run Rate",
            value: Number(
                performance.netRunRate || 0
            ),
        },
    ];

    const trendChartData = trendData.map(
        (row) => ({
            season:
                row.seasonName ||
                "Season",
            wins: Number(
                row.wins || 0
            ),
            losses: Number(
                row.losses || 0
            ),
            winPercentage: Number(
                row.winPercentage || 0
            ),
            runRate: Number(
                row.runRate || 0
            ),
            netRunRate: Number(
                row.netRunRate || 0
            ),
        })
    );

    const selectedCompetitionName =
        competitions.find(
            (competition) =>
                String(competition.id) ===
                String(selectedCompetition)
        )?.name;

    let contextText = "Overall Career";

    if (selectedCompetition !== "overall") {
        contextText =
            selectedCompetitionName ||
            "Selected Competition";

        if (selectedSeason !== "overall") {
            const selectedSeasonObject =
                seasons.find(
                    (season) =>
                        String(season.id) ===
                        String(selectedSeason)
                );

            if (selectedSeasonObject) {
                contextText +=
                    ` • ${selectedSeasonObject.name}`;
            }
        }
    }

    return (
        <div className="page-container team-profile-page">
            <Link
                to="/teams"
                className="back-link"
            >
                ← Back to Teams
            </Link>

            <section className="team-profile-header">
                <div className="team-profile-badge">
                    {teamShortName}
                </div>

                <div>
                    <span className="page-eyebrow">
                        TEAM PROFILE
                    </span>

                    <h1>{teamName}</h1>

                    <p>
                        {teamShortName} • Team
                        performance and analytics
                    </p>
                </div>
            </section>

            <section className="team-filter-section">
                <div className="section-heading">
                    <div>
                        <h2>
                            Performance Filters
                        </h2>

                        <p>
                            Explore this team's
                            performance across
                            competitions and seasons.
                        </p>
                    </div>
                </div>

                <div className="team-filter-grid">
                    <div className="team-filter-group">
                        <label htmlFor="teamCompetition">
                            Competition
                        </label>

                        <select
                            id="teamCompetition"
                            value={
                                selectedCompetition
                            }
                            onChange={
                                handleCompetitionChange
                            }
                        >
                            <option value="overall">
                                Overall Career
                            </option>

                            {competitions.map(
                                (competition) => (
                                    <option
                                        key={
                                            competition.id
                                        }
                                        value={
                                            competition.id
                                        }
                                    >
                                        {
                                            competition.name
                                        }
                                    </option>
                                )
                            )}
                        </select>
                    </div>

                    <div className="team-filter-group">
                        <label htmlFor="teamSeason">
                            Season
                        </label>

                        <select
                            id="teamSeason"
                            value={
                                selectedSeason
                            }
                            onChange={
                                handleSeasonChange
                            }
                            disabled={
                                selectedCompetition ===
                                "overall"
                            }
                        >
                            <option value="overall">
                                All Seasons
                            </option>

                            {filteredSeasons.map(
                                (season) => (
                                    <option
                                        key={
                                            season.id
                                        }
                                        value={
                                            season.id
                                        }
                                    >
                                        {season.name}
                                    </option>
                                )
                            )}
                        </select>
                    </div>
                </div>

                <div className="team-profile-context">
                    <span>Showing</span>
                    <strong>
                        {contextText}
                    </strong>
                </div>
            </section>

            {analyticsLoading && (
                <div className="team-filter-loading">
                    Updating team analytics...
                </div>
            )}

            {error && (
                <div className="team-inline-error">
                    {error}
                </div>
            )}

            <section className="profile-section">
                <div className="section-heading">
                    <div>
                        <h2>Match Record</h2>
                        <p>
                            Results recorded for
                            the selected context.
                        </p>
                    </div>
                </div>

                <div className="team-stat-grid">
                    <div className="team-stat-card">
                        <span>Matches</span>
                        <strong>
                            {formatNumber(
                                matchStats.matches
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>Wins</span>
                        <strong>
                            {formatNumber(
                                matchStats.wins
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>Losses</span>
                        <strong>
                            {formatNumber(
                                matchStats.losses
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>Ties</span>
                        <strong>
                            {formatNumber(
                                matchStats.ties
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>No Results</span>
                        <strong>
                            {formatNumber(
                                matchStats.noResults
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card highlight">
                        <span>
                            Win Percentage
                        </span>
                        <strong>
                            {round(
                                matchStats.winPercentage
                            )}
                            %
                        </strong>
                    </div>

                    {matchStats.points !==
                        undefined && (
                        <div className="team-stat-card">
                            <span>Points</span>
                            <strong>
                                {formatNumber(
                                    matchStats.points
                                )}
                            </strong>
                        </div>
                    )}
                </div>
            </section>

            <section className="profile-section">
                <div className="section-heading">
                    <div>
                        <h2>
                            Scoring Performance
                        </h2>

                        <p>
                            Team scoring and
                            run-rate indicators.
                        </p>
                    </div>
                </div>

                <div className="team-stat-grid">
                    <div className="team-stat-card">
                        <span>Runs Scored</span>
                        <strong>
                            {formatNumber(
                                performance.runsScored
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>
                            Average Runs
                        </span>
                        <strong>
                            {round(
                                performance.averageRuns
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>Run Rate</span>
                        <strong>
                            {round(
                                performance.averageRunRate
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>
                            Runs Conceded
                        </span>
                        <strong>
                            {formatNumber(
                                performance.runsConceded
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>
                            Bowling Rate
                        </span>
                        <strong>
                            {round(
                                performance.bowlingRate
                            )}
                        </strong>
                    </div>

                    <div className="team-stat-card">
                        <span>
                            Net Run Rate
                        </span>
                        <strong>
                            {round(
                                performance.netRunRate
                            )}
                        </strong>
                    </div>
                </div>
            </section>

            <section className="profile-section">
                <div className="section-heading">
                    <div>
                        <h2>
                            Performance Charts
                        </h2>

                        <p>
                            Visual breakdown of
                            results and scoring.
                        </p>
                    </div>
                </div>

                <div className="team-chart-grid">
                    <div className="team-chart-section">
                        <div className="team-chart-heading">
                            <h3>
                                Match Results
                            </h3>

                            <p>
                                Wins, losses,
                                ties and no
                                results.
                            </p>
                        </div>

                        <div className="team-chart-card">
                            {resultData.length >
                            0 ? (
                                <ResponsiveContainer
                                    width="100%"
                                    height={360}
                                >
                                    <PieChart>
                                        <Pie
                                            data={
                                                resultData
                                            }
                                            dataKey="value"
                                            nameKey="name"
                                            cx="50%"
                                            cy="50%"
                                            outerRadius={
                                                120
                                            }
                                            label
                                        />

                                        <Tooltip />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="empty-state">
                                    No result
                                    data
                                    available.
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="team-chart-section">
                        <div className="team-chart-heading">
                            <h3>
                                Scoring Output
                            </h3>

                            <p>
                                Runs,
                                conceded runs
                                and rate
                                indicators.
                            </p>
                        </div>

                        <div className="team-chart-card">
                            <ResponsiveContainer
                                width="100%"
                                height={360}
                            >
                                <BarChart
                                    data={
                                        performanceData
                                    }
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
                </div>
            </section>

            {trendChartData.length > 1 && (
                <section className="profile-section">
                    <div className="section-heading">
                        <div>
                            <h2>
                                Season Performance
                            </h2>

                            <p>
                                Season-by-season
                                wins and losses
                                for the selected
                                competition.
                            </p>
                        </div>
                    </div>

                    <div className="team-chart-card">
                        <ResponsiveContainer
                            width="100%"
                            height={380}
                        >
                            <LineChart
                                data={
                                    trendChartData
                                }
                            >
                                <CartesianGrid
                                    strokeDasharray="3 3"
                                />

                                <XAxis
                                    dataKey="season"
                                />

                                <YAxis />

                                <Tooltip />

                                <Legend />

                                <Line
                                    type="monotone"
                                    dataKey="wins"
                                    name="Wins"
                                    stroke="#2563eb"
                                    strokeWidth={2}
                                />

                                <Line
                                    type="monotone"
                                    dataKey="losses"
                                    name="Losses"
                                    stroke="#ef4444"
                                    strokeWidth={2}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </section>
            )}

            <section className="profile-section">
                <div className="section-heading">
                    <div>
                        <h2>
                            Team Snapshot
                        </h2>

                        <p>
                            Quick interpretation
                            of the selected
                            performance.
                        </p>
                    </div>
                </div>

                <div className="team-insights-grid">
                    <div className="team-insight-card">
                        <span>Win Rate</span>

                        <strong>
                            {round(
                                matchStats.winPercentage
                            )}
                            %
                        </strong>

                        <p>
                            Based on{" "}
                            {formatNumber(
                                matchStats.matches
                            )}{" "}
                            recorded matches.
                        </p>
                    </div>

                    <div className="team-insight-card">
                        <span>
                            Scoring Rate
                        </span>

                        <strong>
                            {round(
                                performance.averageRunRate
                            )}
                        </strong>

                        <p>
                            Average runs scored
                            per over.
                        </p>
                    </div>

                    <div className="team-insight-card">
                        <span>
                            Net Run Rate
                        </span>

                        <strong>
                            {round(
                                performance.netRunRate
                            )}
                        </strong>

                        <p>
                            Difference between
                            scoring and bowling
                            rates.
                        </p>
                    </div>
                </div>
            </section>

            <div className="comparison-footer">
                <Link
                    to="/teams"
                    className="comparison-link"
                >
                    View All Teams
                </Link>

                <Link
                    to="/leaderboards"
                    className="comparison-link"
                >
                    Explore Leaderboards
                </Link>
            </div>
        </div>
    );
}

export default TeamProfile;
