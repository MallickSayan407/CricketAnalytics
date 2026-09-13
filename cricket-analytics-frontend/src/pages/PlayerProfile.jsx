import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
    ResponsiveContainer,
    BarChart,
    Bar,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";

import api from "../services/api";
import "./PlayerProfileTrends.css";


const formatRole = (role) => {
    if (!role) {
        return "Cricketer";
    }

    return role
        .toLowerCase()
        .split("_")
        .map(
            (word) =>
                word.charAt(0).toUpperCase() +
                word.slice(1)
        )
        .join(" ");
};


function PlayerProfile() {

    const { playerId } = useParams();


    const [player, setPlayer] = useState(null);

    const [analytics, setAnalytics] = useState(null);

    const [trend, setTrend] = useState(null);

    const [trendLoading, setTrendLoading] = useState(false);

    const [trendError, setTrendError] = useState("");

    const [competitions, setCompetitions] = useState([]);

    const [seasons, setSeasons] = useState([]);


    const [selectedCompetition, setSelectedCompetition] =
        useState("overall");

    const [selectedSeason, setSelectedSeason] =
        useState("overall");


    const [loading, setLoading] = useState(true);

    const [analyticsLoading, setAnalyticsLoading] =
        useState(false);

    const [error, setError] = useState("");


    /*
     * ============================================================
     * LOAD PLAYER
     * ============================================================
     */

    useEffect(() => {

        const fetchPlayer = async () => {

            try {

                setLoading(true);

                setError("");


                const response =
                    await api.get(`/players/${playerId}`);


                setPlayer(response.data);

            } catch (err) {

                console.error(
                    "Failed to load player:",
                    err
                );


                setError(
                    err.response?.data?.message ||
                    "Failed to load player profile."
                );

            } finally {

                setLoading(false);

            }

        };


        if (playerId) {

            fetchPlayer();

        }

    }, [playerId]);


    /*
     * ============================================================
     * LOAD COMPETITIONS
     * ============================================================
     */

    useEffect(() => {

        const fetchCompetitions = async () => {

            try {

                const response =
                    await api.get("/competitions");


                const data = Array.isArray(response.data)
                    ? response.data
                    : [];


                setCompetitions(data);

            } catch (err) {

                console.error(
                    "Failed to load competitions:",
                    err
                );

            }

        };


        fetchCompetitions();

    }, []);


    /*
     * ============================================================
     * LOAD SEASONS
     * ============================================================
     */

    useEffect(() => {

        const fetchSeasons = async () => {

            try {

                const response =
                    await api.get("/seasons");


                const data = Array.isArray(response.data)
                    ? response.data
                    : [];


                setSeasons(data);

            } catch (err) {

                console.error(
                    "Failed to load seasons:",
                    err
                );

            }

        };


        fetchSeasons();

    }, []);


    /*
     * ============================================================
     * LOAD ANALYTICS
     * ============================================================
     */

    useEffect(() => {

        const fetchAnalytics = async () => {

            if (!playerId) {

                return;

            }


            try {

                setAnalyticsLoading(true);

                setError("");


                let url =
                    `/analytics/players/${playerId}`;


                /*
                 * Overall Career
                 */

                if (
                    selectedCompetition === "overall"
                ) {

                    url =
                        `/analytics/players/${playerId}`;

                }


                /*
                 * Competition
                 */

                else {

                    url =
                        `/analytics/players/${playerId}?competitionId=${selectedCompetition}`;


                    /*
                     * Competition + Season
                     */

                    if (
                        selectedSeason !== "overall"
                    ) {

                        url +=
                            `&seasonId=${selectedSeason}`;

                    }

                }


                const response =
                    await api.get(url);


                setAnalytics(response.data);

            } catch (err) {

                console.error(
                    "Failed to load player analytics:",
                    err
                );


                setAnalytics(null);


                setError(
                    err.response?.data?.message ||
                    "Failed to load player analytics."
                );

            } finally {

                setAnalyticsLoading(false);

            }

        };


        fetchAnalytics();

    }, [
        playerId,
        selectedCompetition,
        selectedSeason,
    ]);


    /*
     * ============================================================
     * LOAD PLAYER TRENDS
     * ============================================================
     */

    useEffect(() => {

        const fetchTrends = async () => {

            if (!playerId) {
                return;
            }

            try {

                setTrendLoading(true);
                setTrendError("");

                let url = `/analytics/players/${playerId}/trends`;

                if (selectedCompetition !== "overall") {

                    url += `?competitionId=${selectedCompetition}`;

                    if (selectedSeason !== "overall") {
                        url += `&seasonId=${selectedSeason}`;
                    }
                }

                const response = await api.get(url);

                setTrend(response.data);

            } catch (err) {

                console.error(
                    "Failed to load player trends:",
                    err
                );

                setTrend(null);
                setTrendError(
                    err.response?.data?.message ||
                    "Failed to load player trends."
                );

            } finally {

                setTrendLoading(false);

            }

        };

        fetchTrends();

    }, [
        playerId,
        selectedCompetition,
        selectedSeason,
    ]);


    /*
     * ============================================================
     * FILTERED SEASONS
     * ============================================================
     */

    const filteredSeasons =
        selectedCompetition === "overall"
            ? []
            : seasons.filter(
                (season) =>
                    String(
                        season.competitionId
                    ) ===
                    String(
                        selectedCompetition
                    )
            );


    /*
     * ============================================================
     * COMPETITION CHANGE
     * ============================================================
     */

    const handleCompetitionChange = (
        event
    ) => {

        const value =
            event.target.value;


        setSelectedCompetition(value);

        setSelectedSeason("overall");

    };


    /*
     * ============================================================
     * SEASON CHANGE
     * ============================================================
     */

    const handleSeasonChange = (
        event
    ) => {

        setSelectedSeason(
            event.target.value
        );

    };


    /*
     * ============================================================
     * LOADING
     * ============================================================
     */

    if (loading) {

        return (

            <div className="page-container">

                <div className="loading-state">

                    Loading player profile...

                </div>

            </div>

        );

    }


    /*
     * ============================================================
     * ERROR
     * ============================================================
     */

    if (error && !analytics) {

        return (

            <div className="page-container">

                <div className="error-state">

                    {error}

                </div>

            </div>

        );

    }


    /*
     * ============================================================
     * PLAYER NOT FOUND
     * ============================================================
     */

    if (!player) {

        return (

            <div className="page-container">

                <div className="empty-state">

                    Player not found.

                </div>

            </div>

        );

    }


    /*
     * ============================================================
     * ANALYTICS DATA
     * ============================================================
     */

    const career =
        analytics?.careerStats || {};


    const performance =
        analytics?.matchPerformance || {};


    /*
     * ============================================================
     * DISPLAY CONTEXT
     * ============================================================
     */

    let displayCompetition =
        "Overall Career";


    if (
        selectedCompetition !== "overall"
    ) {

        const competition =
            competitions.find(
                (item) =>
                    String(item.id) ===
                    String(
                        selectedCompetition
                    )
            );


        displayCompetition =
            competition?.name ||
            "Competition";

    }


    let displaySeason = "";


    if (
        selectedSeason !== "overall"
    ) {

        const season =
            seasons.find(
                (item) =>
                    String(item.id) ===
                    String(selectedSeason)
            );


        displaySeason =
            season?.name || "";

    }


    /*
     * ============================================================
     * CHART DATA
     * ============================================================
     */

    const battingChartData = [

        {
            name: "Runs",
            value: career.runs || 0,
        },

        {
            name: "Fours",
            value: performance.fours || 0,
        },

        {
            name: "Sixes",
            value: performance.sixes || 0,
        },

        {
            name: "50s",
            value: career.fifties || 0,
        },

        {
            name: "100s",
            value: career.centuries || 0,
        },

    ];


    const bowlingChartData = [

        {
            name: "Wickets",
            value: career.wickets || 0,
        },

        {
            name: "5W",
            value:
                career.fiveWicketHauls || 0,
        },

    ];


    /*
     * ============================================================
     * TREND DATA
     * ============================================================
     */

    const recentForm = trend?.recentForm || {};
    const matchTrend = Array.isArray(trend?.matchTrend)
        ? trend.matchTrend
        : [];

    const trendChartData = matchTrend.map((match) => ({
        ...match,
        label: `${match.matchDate || ""} · ${match.opponent || "Unknown"}`,
    }));

    const formatNumber = (value) =>
        value == null ? 0 : value;


    /*
     * ============================================================
     * RENDER
     * ============================================================
     */

    return (

        <div className="page-container">


            {/* =====================================================
                HEADER
            ===================================================== */}

            <div className="page-header">

                <div>

                    <Link
                        to="/players"
                        className="back-link"
                    >
                        ← Players
                    </Link>


                    <h1>

                        {player.name}

                    </h1>


                    <p>

                        {formatRole(player.role)}

                        {player.teamName
                            ? ` · ${player.teamName}`
                            : ""}

                    </p>

                </div>


                <Link
                    to={`/players/${playerId}/comparison`}
                    className="primary-button"
                >
                    Compare Player
                </Link>

            </div>


            {/* =====================================================
                PLAYER PROFILE CARD
            ===================================================== */}

            <section className="player-profile-card">


                <div className="player-avatar-wrapper">

                    {player.avatarUrl ? (

                        <img
                            src={player.avatarUrl}
                            alt={player.name}
                            className="player-avatar"
                        />

                    ) : (

                        <div className="player-avatar-placeholder">

                            {player.name
                                ?.charAt(0)
                                ?.toUpperCase()}

                        </div>

                    )}

                </div>


                <div className="player-profile-info">


                    <h2>

                        {player.name}

                    </h2>


                    <div className="player-meta-grid">


                        <div>

                            <span>
                                Role
                            </span>

                            <strong>
                                {formatRole(player.role)}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Current Team
                            </span>

                            <strong>

                                {player.teamShortName
                                    ? `${player.teamShortName} · ${player.teamName}`
                                    : player.teamName ||
                                    "Not available"}

                            </strong>

                        </div>


                        <div>

                            <span>
                                Batting Style
                            </span>

                            <strong>
                                {player.battingStyle ||
                                    "Not available"}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Bowling Style
                            </span>

                            <strong>
                                {player.bowlingStyle ||
                                    "Not available"}
                            </strong>

                        </div>


                    </div>

                </div>

            </section>


            {/* =====================================================
                ANALYTICS FILTERS
            ===================================================== */}

            <section className="content-section">


                <div className="section-header">

                    <div>

                        <h2>
                            Performance Filters
                        </h2>

                        <p>
                            Explore performance by
                            competition and season.
                        </p>

                    </div>

                </div>


                <div className="filter-grid">


                    {/* Competition */}

                    <div className="filter-group">

                        <label htmlFor="competition">

                            Competition

                        </label>


                        <select
                            id="competition"
                            value={
                                selectedCompetition
                            }
                            onChange={
                                handleCompetitionChange
                            }
                            className="filter-select"
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
                                        {competition.name}
                                    </option>

                                )
                            )}

                        </select>

                    </div>


                    {/* Season */}

                    <div className="filter-group">

                        <label htmlFor="season">

                            Season

                        </label>


                        <select
                            id="season"
                            value={
                                selectedSeason
                            }
                            onChange={
                                handleSeasonChange
                            }
                            className="filter-select"
                            disabled={
                                selectedCompetition ===
                                "overall" ||
                                filteredSeasons.length ===
                                0
                            }
                        >

                            <option value="overall">

                                Overall Competition

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


                {/* Active filter */}

                <div className="filter-summary">

                    <span>
                        Showing:
                    </span>

                    <strong>

                        {displayCompetition}

                        {displaySeason
                            ? ` · ${displaySeason}`
                            : ""}

                    </strong>

                </div>

            </section>


            {/* =====================================================
                ANALYTICS LOADING
            ===================================================== */}

            {analyticsLoading && (

                <div className="status-message">

                    Loading selected statistics...

                </div>

            )}


            {/* =====================================================
                CAREER OVERVIEW
            ===================================================== */}

            {!analyticsLoading && analytics && (

                <>


                    <section className="content-section">


                        <div className="section-header">

                            <div>

                                <h2>
                                    Career Overview
                                </h2>

                                <p>

                                    {displayCompetition}

                                    {displaySeason
                                        ? ` · ${displaySeason}`
                                        : ""}

                                </p>

                            </div>

                        </div>


                        <div className="stats-grid">


                            <div className="stat-card">

                                <span className="stat-label">
                                    Matches
                                </span>

                                <strong>
                                    {career.matches ||
                                        0}
                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    Runs
                                </span>

                                <strong>
                                    {career.runs ||
                                        0}
                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    Batting Average
                                </span>

                                <strong>

                                    {career.battingAverage !=
                                        null
                                        ? career.battingAverage.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    Strike Rate
                                </span>

                                <strong>

                                    {career.strikeRate !=
                                        null
                                        ? career.strikeRate.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    Highest Score
                                </span>

                                <strong>
                                    {career.highestScore ||
                                        0}
                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    50s
                                </span>

                                <strong>
                                    {career.fifties ||
                                        0}
                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    100s
                                </span>

                                <strong>
                                    {career.centuries ||
                                        0}
                                </strong>

                            </div>


                            <div className="stat-card">

                                <span className="stat-label">
                                    Wickets
                                </span>

                                <strong>
                                    {career.wickets ||
                                        0}
                                </strong>

                            </div>


                        </div>

                    </section>


                    {/* =================================================
                        BATTING
                    ================================================= */}

                    <section className="content-section">


                        <div className="section-header">

                            <div>

                                <h2>
                                    Batting Statistics
                                </h2>

                                <p>
                                    Batting performance
                                </p>

                            </div>

                        </div>


                        <div className="info-grid">


                            <div className="info-item">

                                <span>
                                    Runs
                                </span>

                                <strong>
                                    {career.runs ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Matches
                                </span>

                                <strong>
                                    {career.matches ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Highest Score
                                </span>

                                <strong>
                                    {career.highestScore ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Not Outs
                                </span>

                                <strong>
                                    {career.notOuts ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Average
                                </span>

                                <strong>

                                    {career.battingAverage !=
                                        null
                                        ? career.battingAverage.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Strike Rate
                                </span>

                                <strong>

                                    {career.strikeRate !=
                                        null
                                        ? career.strikeRate.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Fours
                                </span>

                                <strong>
                                    {performance.fours ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Sixes
                                </span>

                                <strong>
                                    {performance.sixes ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Fifties
                                </span>

                                <strong>
                                    {career.fifties ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Centuries
                                </span>

                                <strong>
                                    {career.centuries ||
                                        0}
                                </strong>

                            </div>


                        </div>


                        <div className="chart-container">

                            <ResponsiveContainer
                                width="100%"
                                height={350}
                            >

                                <BarChart
                                    data={
                                        battingChartData
                                    }
                                >

                                    <CartesianGrid
                                        strokeDasharray="3 3"
                                    />

                                    <XAxis
                                        dataKey="name"
                                    />

                                    <YAxis />

                                    <Tooltip />

                                    <Bar
                                        dataKey="value"
                                        name="Batting"
                                    />

                                </BarChart>

                            </ResponsiveContainer>

                        </div>

                    </section>


                    {/* =================================================
                        BOWLING
                    ================================================= */}

                    <section className="content-section">


                        <div className="section-header">

                            <div>

                                <h2>
                                    Bowling Statistics
                                </h2>

                                <p>
                                    Bowling performance
                                </p>

                            </div>

                        </div>


                        <div className="info-grid">


                            <div className="info-item">

                                <span>
                                    Wickets
                                </span>

                                <strong>
                                    {career.wickets ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Runs Conceded
                                </span>

                                <strong>
                                    {career.runsConceded ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Economy
                                </span>

                                <strong>

                                    {career.economy !=
                                        null
                                        ? career.economy.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Bowling Average
                                </span>

                                <strong>

                                    {career.bowlingAverage !=
                                        null
                                        ? career.bowlingAverage.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Five-Wicket Hauls
                                </span>

                                <strong>
                                    {career.fiveWicketHauls ||
                                        0}
                                </strong>

                            </div>


                        </div>


                        <div className="chart-container">

                            <ResponsiveContainer
                                width="100%"
                                height={300}
                            >

                                <BarChart
                                    data={
                                        bowlingChartData
                                    }
                                >

                                    <CartesianGrid
                                        strokeDasharray="3 3"
                                    />

                                    <XAxis
                                        dataKey="name"
                                    />

                                    <YAxis />

                                    <Tooltip />

                                    <Bar
                                        dataKey="value"
                                        name="Bowling"
                                    />

                                </BarChart>

                            </ResponsiveContainer>

                        </div>

                    </section>


                    {/* =================================================
                        MATCH PERFORMANCE
                    ================================================= */}

                    <section className="content-section">


                        <div className="section-header">

                            <div>

                                <h2>
                                    Match Performance
                                </h2>

                                <p>
                                    Aggregated match-level
                                    statistics
                                </p>

                            </div>

                        </div>


                        <div className="info-grid">


                            <div className="info-item">

                                <span>
                                    Matches
                                </span>

                                <strong>
                                    {performance.matches ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Balls Faced
                                </span>

                                <strong>
                                    {performance.ballsFaced ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Runs
                                </span>

                                <strong>
                                    {performance.runs ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Fours
                                </span>

                                <strong>
                                    {performance.fours ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Sixes
                                </span>

                                <strong>
                                    {performance.sixes ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Strike Rate
                                </span>

                                <strong>

                                    {performance.averageStrikeRate !=
                                        null
                                        ? performance.averageStrikeRate.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Wickets
                                </span>

                                <strong>
                                    {performance.wickets ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Runs Conceded
                                </span>

                                <strong>
                                    {performance.runsConceded ||
                                        0}
                                </strong>

                            </div>


                            <div className="info-item">

                                <span>
                                    Economy
                                </span>

                                <strong>

                                    {performance.averageEconomy !=
                                        null
                                        ? performance.averageEconomy.toFixed(
                                            2
                                        )
                                        : "-"}

                                </strong>

                            </div>


                        </div>

                    </section>

                </>

            )}


            {/* =====================================================
                PLAYER TRENDS
            ===================================================== */}

            <section className="content-section player-trends-section">

                <div className="section-header">
                    <div>
                        <h2>Player Trends</h2>
                        <p>Recent form and match-by-match performance.</p>
                    </div>
                </div>

                {trendLoading && (
                    <div className="status-message">
                        Loading performance trends...
                    </div>
                )}

                {!trendLoading && trendError && (
                    <div className="status-message trend-error">
                        {trendError}
                    </div>
                )}

                {!trendLoading && !trendError && trend && (
                    <>

                        <div className="section-subheader">
                            <h3>Recent Form</h3>
                            <span>Last {recentForm.matches || 0} matches</span>
                        </div>

                        <div className="stats-grid trend-form-grid">
                            <div className="stat-card">
                                <span className="stat-label">Matches</span>
                                <strong>{formatNumber(recentForm.matches)}</strong>
                            </div>
                            <div className="stat-card">
                                <span className="stat-label">Runs</span>
                                <strong>{formatNumber(recentForm.runs)}</strong>
                            </div>
                            <div className="stat-card">
                                <span className="stat-label">Avg Runs</span>
                                <strong>{recentForm.averageRuns != null ? Number(recentForm.averageRuns).toFixed(2) : "-"}</strong>
                            </div>
                            <div className="stat-card">
                                <span className="stat-label">Avg Strike Rate</span>
                                <strong>{recentForm.averageStrikeRate != null ? Number(recentForm.averageStrikeRate).toFixed(2) : "-"}</strong>
                            </div>
                            <div className="stat-card">
                                <span className="stat-label">Fours</span>
                                <strong>{formatNumber(recentForm.fours)}</strong>
                            </div>
                            <div className="stat-card">
                                <span className="stat-label">Sixes</span>
                                <strong>{formatNumber(recentForm.sixes)}</strong>
                            </div>
                            <div className="stat-card">
                                <span className="stat-label">Wickets</span>
                                <strong>{formatNumber(recentForm.wickets)}</strong>
                            </div>
                            <div className="stat-card trend-score-card">
                                <span className="stat-label">Form Score</span>
                                <strong>{recentForm.formScore != null ? Number(recentForm.formScore).toFixed(2) : "-"}</strong>
                            </div>
                        </div>

                        <div className="trend-chart-grid">

                            <div className="trend-chart-card">
                                <div className="trend-chart-header">
                                    <h3>Runs by Match</h3>
                                    <span>Batting output</span>
                                </div>
                                <div className="chart-container">
                                    <ResponsiveContainer width="100%" height={320}>
                                        <LineChart data={trendChartData}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="matchDate" />
                                            <YAxis />
                                            <Tooltip
                                                labelFormatter={(label, payload) => {
                                                    const item = payload?.[0]?.payload;
                                                    return item
                                                        ? `${item.matchDate} · vs ${item.opponent}`
                                                        : label;
                                                }}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="runs"
                                                name="Runs"
                                                strokeWidth={2}
                                                dot={{ r: 3 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                            <div className="trend-chart-card">
                                <div className="trend-chart-header">
                                    <h3>Strike Rate by Match</h3>
                                    <span>Batting efficiency</span>
                                </div>
                                <div className="chart-container">
                                    <ResponsiveContainer width="100%" height={320}>
                                        <LineChart data={trendChartData}>
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis dataKey="matchDate" />
                                            <YAxis />
                                            <Tooltip
                                                labelFormatter={(label, payload) => {
                                                    const item = payload?.[0]?.payload;
                                                    return item
                                                        ? `${item.matchDate} · vs ${item.opponent}`
                                                        : label;
                                                }}
                                            />
                                            <Line
                                                type="monotone"
                                                dataKey="strikeRate"
                                                name="Strike Rate"
                                                strokeWidth={2}
                                                dot={{ r: 3 }}
                                            />
                                        </LineChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>

                        </div>

                        <div className="trend-chart-card trend-wickets-card">
                            <div className="trend-chart-header">
                                <h3>Wickets by Match</h3>
                                <span>Bowling contribution</span>
                            </div>
                            <div className="chart-container">
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={trendChartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis dataKey="matchDate" />
                                        <YAxis allowDecimals={false} />
                                        <Tooltip
                                            labelFormatter={(label, payload) => {
                                                const item = payload?.[0]?.payload;
                                                return item
                                                    ? `${item.matchDate} · vs ${item.opponent}`
                                                    : label;
                                            }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="wickets"
                                            name="Wickets"
                                            strokeWidth={2}
                                            dot={{ r: 3 }}
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className="section-subheader trend-table-heading">
                            <h3>Match-by-Match Performance</h3>
                            <span>{matchTrend.length} matches</span>
                        </div>

                        {matchTrend.length > 0 ? (
                            <div className="table-wrapper trend-table-wrapper">
                                <table className="data-table trend-table">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Opponent</th>
                                            <th>Team</th>
                                            <th>Runs</th>
                                            <th>Balls</th>
                                            <th>SR</th>
                                            <th>4s</th>
                                            <th>6s</th>
                                            <th>Wkts</th>
                                            <th>Economy</th>
                                            <th>Match</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {matchTrend.map((match) => (
                                            <tr key={match.matchId}>
                                                <td>{match.matchDate || "-"}</td>
                                                <td>{match.opponent || "-"}</td>
                                                <td>{match.teamName || "-"}</td>
                                                <td>{formatNumber(match.runs)}</td>
                                                <td>{formatNumber(match.ballsFaced)}</td>
                                                <td>{match.strikeRate != null ? Number(match.strikeRate).toFixed(2) : "-"}</td>
                                                <td>{formatNumber(match.fours)}</td>
                                                <td>{formatNumber(match.sixes)}</td>
                                                <td>{formatNumber(match.wickets)}</td>
                                                <td>{match.bowlingEconomy != null ? Number(match.bowlingEconomy).toFixed(2) : "-"}</td>
                                                <td>
                                                    <Link
                                                        to={`/matches/${match.matchId}`}
                                                        className="table-link"
                                                    >
                                                        View
                                                    </Link>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="empty-state">
                                No match-level trend data is available for this selection.
                            </div>
                        )}

                    </>
                )}

            </section>


            {/* =====================================================
                EXPLORE MORE
            ===================================================== */}

            <section className="content-section">


                <div className="section-header">

                    <h2>
                        Explore More
                    </h2>

                </div>


                <div className="action-grid">


                    <Link
                        to={`/players/${playerId}/comparison`}
                        className="action-card"
                    >

                        <h3>
                            Compare Player
                        </h3>

                        <p>
                            Compare this player with
                            other cricketers across
                            competitions and seasons.
                        </p>

                    </Link>


                    {player.teamId && (

                        <Link
                            to={`/teams/${player.teamId}`}
                            className="action-card"
                        >

                            <h3>
                                View Team
                            </h3>

                            <p>
                                Explore team analytics,
                                results and performance.
                            </p>

                        </Link>

                    )}


                    <Link
                        to="/leaderboards"
                        className="action-card"
                    >

                        <h3>
                            Leaderboards
                        </h3>

                        <p>
                            See how this player ranks
                            among other players.
                        </p>

                    </Link>


                </div>

            </section>


        </div>

    );

}


export default PlayerProfile;