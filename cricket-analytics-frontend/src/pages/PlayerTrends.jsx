import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    BarChart,
    Bar,
} from "recharts";

import api from "../services/api";

function PlayerTrends() {

    const { playerId } = useParams();

    const [player, setPlayer] = useState(null);
    const [competitions, setCompetitions] = useState([]);
    const [seasons, setSeasons] = useState([]);

    const [selectedCompetition, setSelectedCompetition] =
        useState("overall");

    const [selectedSeason, setSelectedSeason] =
        useState("overall");

    const [trendData, setTrendData] = useState(null);

    const [loading, setLoading] = useState(true);
    const [trendLoading, setTrendLoading] = useState(false);

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
                    "Failed to load player."
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

                setCompetitions(
                    Array.isArray(response.data)
                        ? response.data
                        : []
                );

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

                setSeasons(
                    Array.isArray(response.data)
                        ? response.data
                        : []
                );

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
     * FILTERED SEASONS
     * ============================================================
     */

    const filteredSeasons = useMemo(() => {

        if (selectedCompetition === "overall") {
            return [];
        }

        return seasons.filter(
            (season) =>
                String(season.competitionId) ===
                String(selectedCompetition)
        );

    }, [
        seasons,
        selectedCompetition
    ]);


    /*
     * ============================================================
     * LOAD TRENDS
     * ============================================================
     */

    useEffect(() => {

        const fetchTrends = async () => {

            if (!playerId) {
                return;
            }

            try {

                setTrendLoading(true);
                setError("");

                let url =
                    `/analytics/players/${playerId}/trends`;

                if (
                    selectedCompetition !==
                    "overall"
                ) {

                    url +=
                        `?competitionId=${selectedCompetition}`;

                    if (
                        selectedSeason !==
                        "overall"
                    ) {

                        url +=
                            `&seasonId=${selectedSeason}`;

                    }

                }

                const response =
                    await api.get(url);

                setTrendData(response.data);

            } catch (err) {

                console.error(
                    "Failed to load player trends:",
                    err
                );

                setTrendData(null);

                setError(
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
        selectedSeason
    ]);


    /*
     * ============================================================
     * FILTER HANDLERS
     * ============================================================
     */

    const handleCompetitionChange = (event) => {

        const value =
            event.target.value;

        setSelectedCompetition(value);
        setSelectedSeason("overall");

    };


    const handleSeasonChange = (event) => {

        setSelectedSeason(
            event.target.value
        );

    };


    /*
     * ============================================================
     * DISPLAY CONTEXT
     * ============================================================
     */

    const displayCompetition =
        selectedCompetition === "overall"
            ? "Overall Career"
            : (
                competitions.find(
                    (competition) =>
                        String(competition.id) ===
                        String(selectedCompetition)
                )?.name || "Competition"
            );


    const displaySeason =
        selectedSeason === "overall"
            ? ""
            : (
                seasons.find(
                    (season) =>
                        String(season.id) ===
                        String(selectedSeason)
                )?.name || ""
            );


    /*
     * ============================================================
     * TREND DATA
     * ============================================================
     */

    const matchTrend =
        trendData?.matchTrend || [];

    const recentForm =
        trendData?.recentForm || {};


    /*
     * ============================================================
     * CHART DATA
     * ============================================================
     */

    const battingTrendData = matchTrend.map(
        (match, index) => ({
            ...match,
            matchNumber: index + 1,
            label:
                match.matchDate ||
                `Match ${index + 1}`,
            runs: match.runs || 0,
            strikeRate:
                match.strikeRate || 0,
        })
    );


    const bowlingTrendData = matchTrend
        .filter(
            (match) =>
                (match.wickets || 0) > 0 ||
                (match.runsConceded || 0) > 0
        )
        .map(
            (match, index) => ({
                ...match,
                matchNumber: index + 1,
                label:
                    match.matchDate ||
                    `Match ${index + 1}`,
                wickets: match.wickets || 0,
                economy:
                    match.bowlingEconomy || 0,
            })
        );


    /*
     * ============================================================
     * LOADING
     * ============================================================
     */

    if (loading) {

        return (
            <div className="page-container">

                <div className="status-message">
                    Loading player trends...
                </div>

            </div>
        );

    }


    /*
     * ============================================================
     * ERROR
     * ============================================================
     */

    if (error && !trendData) {

        return (
            <div className="page-container">

                <div className="status-message error">
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
                        to={`/players/${playerId}`}
                        className="back-link"
                    >
                        ← Player Profile
                    </Link>

                    <h1>
                        {player.name}
                    </h1>

                    <p>
                        {player.role || "Cricketer"}

                        {player.teamName
                            ? ` · ${player.teamName}`
                            : ""}
                    </p>

                </div>


                <div className="trend-header-actions">

                    <Link
                        to={`/players/${playerId}/comparison`}
                        className="primary-button"
                    >
                        Compare Player
                    </Link>

                </div>

            </div>


            {/* =====================================================
                FILTERS
            ===================================================== */}

            <section className="content-section">

                <div className="section-header">

                    <div>

                        <h2>
                            Performance Trends
                        </h2>

                        <p>
                            Track match-by-match performance
                            across competitions and seasons.
                        </p>

                    </div>

                </div>


                <div className="filter-grid">

                    <div className="filter-group">

                        <label htmlFor="trend-competition">
                            Competition
                        </label>

                        <select
                            id="trend-competition"
                            value={selectedCompetition}
                            onChange={
                                handleCompetitionChange
                            }
                            className="filter-select"
                        >

                            <option value="overall">
                                Overall
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


                    <div className="filter-group">

                        <label htmlFor="trend-season">
                            Season
                        </label>

                        <select
                            id="trend-season"
                            value={selectedSeason}
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
                                        key={season.id}
                                        value={season.id}
                                    >
                                        {season.name}
                                    </option>

                                )
                            )}

                        </select>

                    </div>

                </div>


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
                LOADING
            ===================================================== */}

            {trendLoading && (

                <div className="status-message">
                    Loading selected trends...
                </div>

            )}


            {!trendLoading && trendData && (

                <>

                    {/* =================================================
                        RECENT FORM
                    ================================================= */}

                    <section className="content-section">

                        <div className="section-header">

                            <div>

                                <h2>
                                    Recent Form
                                </h2>

                                <p>
                                    Performance across the
                                    five most recent matches.
                                </p>

                            </div>

                        </div>


                        <div className="form-stat-grid">

                            <div className="form-stat-card">

                                <span>
                                    Matches
                                </span>

                                <strong>
                                    {recentForm.matches || 0}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Runs
                                </span>

                                <strong>
                                    {recentForm.runs || 0}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Average Runs
                                </span>

                                <strong>
                                    {recentForm.averageRuns != null
                                        ? recentForm.averageRuns.toFixed(2)
                                        : "0.00"}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Strike Rate
                                </span>

                                <strong>
                                    {recentForm.averageStrikeRate != null
                                        ? recentForm.averageStrikeRate.toFixed(2)
                                        : "0.00"}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Fours
                                </span>

                                <strong>
                                    {recentForm.fours || 0}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Sixes
                                </span>

                                <strong>
                                    {recentForm.sixes || 0}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Wickets
                                </span>

                                <strong>
                                    {recentForm.wickets || 0}
                                </strong>

                            </div>


                            <div className="form-stat-card">

                                <span>
                                    Form Score
                                </span>

                                <strong>
                                    {recentForm.formScore != null
                                        ? `${recentForm.formScore.toFixed(1)} / 100`
                                        : "0.0 / 100"}
                                </strong>

                            </div>

                        </div>

                    </section>


                    {/* =================================================
                        RUNS TREND
                    ================================================= */}

                    <section className="content-section">

                        <div className="section-header">

                            <div>

                                <h2>
                                    Runs Trend
                                </h2>

                                <p>
                                    Match-by-match batting output.
                                </p>

                            </div>

                        </div>


                        {battingTrendData.length > 0 ? (

                            <div className="chart-container">

                                <ResponsiveContainer
                                    width="100%"
                                    height={380}
                                >

                                    <LineChart
                                        data={
                                            battingTrendData
                                        }
                                        margin={{
                                            top: 10,
                                            right: 20,
                                            left: 0,
                                            bottom: 10
                                        }}
                                    >

                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                        />

                                        <XAxis
                                            dataKey="matchNumber"
                                            label={{
                                                value: "Match",
                                                position:
                                                    "insideBottom",
                                                offset: -5
                                            }}
                                        />

                                        <YAxis
                                            label={{
                                                value: "Runs",
                                                angle: -90,
                                                position:
                                                    "insideLeft"
                                            }}
                                        />

                                        <Tooltip
                                            labelFormatter={
                                                (value) =>
                                                    `Match ${value}`
                                            }
                                            formatter={
                                                (value) =>
                                                    [
                                                        value,
                                                        "Runs"
                                                    ]
                                            }
                                        />

                                        <Line
                                            type="monotone"
                                            dataKey="runs"
                                            name="Runs"
                                            strokeWidth={2}
                                            dot={{
                                                r: 4
                                            }}
                                        />

                                    </LineChart>

                                </ResponsiveContainer>

                            </div>

                        ) : (

                            <div className="empty-state">
                                No match trend data available.
                            </div>

                        )}

                    </section>


                    {/* =================================================
                        STRIKE RATE TREND
                    ================================================= */}

                    <section className="content-section">

                        <div className="section-header">

                            <div>

                                <h2>
                                    Strike Rate Trend
                                </h2>

                                <p>
                                    Match-by-match batting strike rate.
                                </p>

                            </div>

                        </div>


                        {battingTrendData.length > 0 ? (

                            <div className="chart-container">

                                <ResponsiveContainer
                                    width="100%"
                                    height={350}
                                >

                                    <LineChart
                                        data={
                                            battingTrendData
                                        }
                                    >

                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                        />

                                        <XAxis
                                            dataKey="matchNumber"
                                        />

                                        <YAxis />

                                        <Tooltip
                                            labelFormatter={
                                                (value) =>
                                                    `Match ${value}`
                                            }
                                            formatter={
                                                (value) =>
                                                    [
                                                        value,
                                                        "Strike Rate"
                                                    ]
                                            }
                                        />

                                        <Line
                                            type="monotone"
                                            dataKey="strikeRate"
                                            name="Strike Rate"
                                            strokeWidth={2}
                                            dot={{
                                                r: 3
                                            }}
                                        />

                                    </LineChart>

                                </ResponsiveContainer>

                            </div>

                        ) : (

                            <div className="empty-state">
                                No strike-rate data available.
                            </div>

                        )}

                    </section>


                    {/* =================================================
                        BOWLING TREND
                    ================================================= */}

                    <section className="content-section">

                        <div className="section-header">

                            <div>

                                <h2>
                                    Bowling Trend
                                </h2>

                                <p>
                                    Wickets taken and bowling
                                    economy across matches.
                                </p>

                            </div>

                        </div>


                        {bowlingTrendData.length > 0 ? (

                            <div className="chart-container">

                                <ResponsiveContainer
                                    width="100%"
                                    height={350}
                                >

                                    <BarChart
                                        data={
                                            bowlingTrendData
                                        }
                                    >

                                        <CartesianGrid
                                            strokeDasharray="3 3"
                                        />

                                        <XAxis
                                            dataKey="matchNumber"
                                        />

                                        <YAxis />

                                        <Tooltip
                                            labelFormatter={
                                                (value) =>
                                                    `Bowling Match ${value}`
                                            }
                                        />

                                        <Bar
                                            dataKey="wickets"
                                            name="Wickets"
                                        />

                                    </BarChart>

                                </ResponsiveContainer>

                            </div>

                        ) : (

                            <div className="empty-state">
                                No bowling data available for
                                this selection.
                            </div>

                        )}

                    </section>


                    {/* =================================================
                        MATCH TABLE
                    ================================================= */}

                    <section className="content-section">

                        <div className="section-header">

                            <div>

                                <h2>
                                    Match-by-Match Performance
                                </h2>

                                <p>
                                    Detailed performance for
                                    every available match.
                                </p>

                            </div>

                        </div>


                        {matchTrend.length > 0 ? (

                            <div className="table-container">

                                <table className="analytics-table">

                                    <thead>

                                        <tr>

                                            <th>
                                                Date
                                            </th>

                                            <th>
                                                Opponent
                                            </th>

                                            <th>
                                                Team
                                            </th>

                                            <th>
                                                Runs
                                            </th>

                                            <th>
                                                BF
                                            </th>

                                            <th>
                                                SR
                                            </th>

                                            <th>
                                                4s
                                            </th>

                                            <th>
                                                6s
                                            </th>

                                            <th>
                                                Wkts
                                            </th>

                                            <th>
                                                Econ
                                            </th>

                                        </tr>

                                    </thead>


                                    <tbody>

                                        {matchTrend
                                            .slice()
                                            .reverse()
                                            .map(
                                                (match) => (

                                                    <tr
                                                        key={
                                                            match.matchId
                                                        }
                                                    >

                                                        <td>
                                                            {
                                                                match.matchDate ||
                                                                "-"
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.opponent ||
                                                                "-"
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.teamName ||
                                                                "-"
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.runs ??
                                                                0
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.ballsFaced ??
                                                                0
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.strikeRate !=
                                                                null
                                                                    ? match.strikeRate.toFixed(
                                                                          2
                                                                      )
                                                                    : "-"
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.fours ??
                                                                0
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.sixes ??
                                                                0
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.wickets ??
                                                                0
                                                            }
                                                        </td>

                                                        <td>
                                                            {
                                                                match.bowlingEconomy !=
                                                                null
                                                                    ? match.bowlingEconomy.toFixed(
                                                                          2
                                                                      )
                                                                    : "-"
                                                            }
                                                        </td>

                                                    </tr>

                                                )
                                            )}

                                    </tbody>

                                </table>

                            </div>

                        ) : (

                            <div className="empty-state">
                                No match performance available.
                            </div>

                        )}

                    </section>


                    {/* =================================================
                        EXPLORE MORE
                    ================================================= */}

                    <section className="content-section">

                        <div className="section-header">

                            <h2>
                                Explore More
                            </h2>

                        </div>


                        <div className="action-grid">

                            <Link
                                to={`/players/${playerId}`}
                                className="action-card"
                            >

                                <h3>
                                    Player Profile
                                </h3>

                                <p>
                                    View career statistics,
                                    batting and bowling analysis.
                                </p>

                            </Link>


                            <Link
                                to={`/players/${playerId}/comparison`}
                                className="action-card"
                            >

                                <h3>
                                    Compare Player
                                </h3>

                                <p>
                                    Compare this player with
                                    other cricketers.
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
                                        Explore team analytics
                                        and performance.
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
                                    against other players.
                                </p>

                            </Link>

                        </div>

                    </section>

                </>

            )}

        </div>

    );
}

export default PlayerTrends;