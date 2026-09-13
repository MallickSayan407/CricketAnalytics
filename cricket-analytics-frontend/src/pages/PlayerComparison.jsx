import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
    ResponsiveContainer,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from "recharts";
import api from "../services/api";

function PlayerComparison() {
    const { playerId } = useParams();

    const [players, setPlayers] = useState([]);

    const [selectedPlayer1, setSelectedPlayer1] = useState(
        playerId || ""
    );

    const [selectedPlayer2, setSelectedPlayer2] = useState("");

    /* ============================================================
       COMPETITION + SEASON FILTERS
       ============================================================ */

    const [competitions, setCompetitions] = useState([]);
    const [seasons, setSeasons] = useState([]);

    const [selectedCompetition, setSelectedCompetition] =
        useState("");

    const [selectedSeason, setSelectedSeason] =
        useState("");

    const [comparison, setComparison] = useState(null);

    const [loadingPlayers, setLoadingPlayers] =
        useState(true);

    const [loadingFilters, setLoadingFilters] =
        useState(true);

    const [loadingComparison, setLoadingComparison] =
        useState(false);

    const [error, setError] = useState("");

    /* ============================================================
       LOAD PLAYERS
       ============================================================ */

    useEffect(() => {
        const fetchPlayers = async () => {
            try {
                setLoadingPlayers(true);
                setError("");

                const response =
                    await api.get("/players");

                const data = Array.isArray(response.data)
                    ? response.data
                    : [];

                setPlayers(data);

                /*
                 * If opened from a Player Profile,
                 * keep that player selected.
                 */
                if (playerId) {
                    const exists = data.some(
                        (player) =>
                            String(player.id) ===
                            String(playerId)
                    );

                    if (exists) {
                        setSelectedPlayer1(
                            String(playerId)
                        );
                    }
                }

                /*
                 * Automatically choose another player
                 * for Player 2.
                 */
                if (!selectedPlayer2 && data.length > 1) {
                    const firstOtherPlayer =
                        data.find(
                            (player) =>
                                String(player.id) !==
                                String(playerId)
                        );

                    if (firstOtherPlayer) {
                        setSelectedPlayer2(
                            String(firstOtherPlayer.id)
                        );
                    }
                }
            } catch (err) {
                console.error(
                    "Failed to load players:",
                    err
                );

                setError(
                    err.response?.data?.message ||
                        "Failed to load players."
                );
            } finally {
                setLoadingPlayers(false);
            }
        };

        fetchPlayers();
    }, [playerId]);

    /* ============================================================
       LOAD COMPETITIONS + SEASONS
       ============================================================ */

    useEffect(() => {
        const fetchFilters = async () => {
            try {
                setLoadingFilters(true);

                const [
                    competitionResponse,
                    seasonResponse,
                ] = await Promise.all([
                    api.get("/competitions"),
                    api.get("/seasons"),
                ]);

                const competitionData =
                    Array.isArray(
                        competitionResponse.data
                    )
                        ? competitionResponse.data
                        : [];

                const seasonData =
                    Array.isArray(seasonResponse.data)
                        ? seasonResponse.data
                        : [];

                setCompetitions(competitionData);
                setSeasons(seasonData);
            } catch (err) {
                console.error(
                    "Failed to load competition filters:",
                    err
                );

                setError(
                    err.response?.data?.message ||
                        "Failed to load competition filters."
                );
            } finally {
                setLoadingFilters(false);
            }
        };

        fetchFilters();
    }, []);

    /* ============================================================
       FILTERED SEASONS
       ============================================================ */

    const filteredSeasons = useMemo(() => {
        if (!selectedCompetition) {
            return [];
        }

        return seasons.filter(
            (season) =>
                String(season.competitionId) ===
                String(selectedCompetition)
        );
    }, [seasons, selectedCompetition]);

    /* ============================================================
       COMPETITION CHANGE
       ============================================================ */

    const handleCompetitionChange = (event) => {
        const value = event.target.value;

        setSelectedCompetition(value);

        /*
         * Reset season whenever competition changes.
         * This prevents an old season from belonging
         * to the newly selected competition.
         */
        setSelectedSeason("");
        setComparison(null);
        setError("");
    };

    /* ============================================================
       SEASON CHANGE
       ============================================================ */

    const handleSeasonChange = (event) => {
        setSelectedSeason(event.target.value);
        setComparison(null);
        setError("");
    };

    /* ============================================================
       COMPARE PLAYERS
       ============================================================ */

    const comparePlayers = async () => {
        if (!selectedPlayer1 || !selectedPlayer2) {
            setError(
                "Please select two players to compare."
            );
            return;
        }

        if (
            String(selectedPlayer1) ===
            String(selectedPlayer2)
        ) {
            setError(
                "Please select two different players."
            );
            return;
        }

        try {
            setLoadingComparison(true);
            setError("");

            /*
             * Build query parameters safely.
             */
            const params = new URLSearchParams();

            params.append(
                "playerIds",
                selectedPlayer1
            );

            params.append(
                "playerIds",
                selectedPlayer2
            );

            if (selectedCompetition) {
                params.append(
                    "competitionId",
                    selectedCompetition
                );
            }

            if (
                selectedCompetition &&
                selectedSeason
            ) {
                params.append(
                    "seasonId",
                    selectedSeason
                );
            }

            const response = await api.get(
                `/analytics/players/compare?${params.toString()}`
            );

            const data = response.data;

            if (
                !data ||
                !Array.isArray(data.players) ||
                data.players.length < 2
            ) {
                setComparison(null);

                setError(
                    "The comparison API did not return two players."
                );

                return;
            }

            setComparison(data);
        } catch (err) {
            console.error(
                "Failed to compare players:",
                err
            );

            setComparison(null);

            setError(
                err.response?.data?.message ||
                    "Failed to compare players."
            );
        } finally {
            setLoadingComparison(false);
        }
    };

    /* ============================================================
       AUTOMATIC INITIAL / FILTERED COMPARISON
       ============================================================ */

    useEffect(() => {
        if (
            !loadingPlayers &&
            !loadingFilters &&
            selectedPlayer1 &&
            selectedPlayer2 &&
            String(selectedPlayer1) !==
                String(selectedPlayer2)
        ) {
            comparePlayers();
        }
    }, [
        loadingPlayers,
        loadingFilters,
        selectedPlayer1,
        selectedPlayer2,
        selectedCompetition,
        selectedSeason,
    ]);

    /* ============================================================
       SELECTED PLAYER OBJECTS
       ============================================================ */

    const playerOne = useMemo(
        () =>
            comparison?.players?.[0] || null,
        [comparison]
    );

    const playerTwo = useMemo(
        () =>
            comparison?.players?.[1] || null,
        [comparison]
    );

    /* ============================================================
       HELPERS
       ============================================================ */

    const formatNumber = (value) => {
        if (
            value === null ||
            value === undefined
        ) {
            return "-";
        }

        return Number(value).toLocaleString(
            "en-IN"
        );
    };

    const formatDecimal = (
        value,
        digits = 2
    ) => {
        if (
            value === null ||
            value === undefined ||
            Number.isNaN(Number(value))
        ) {
            return "-";
        }

        return Number(value).toFixed(digits);
    };

    /* ============================================================
       CURRENT FILTER LABEL
       ============================================================ */

    const selectedCompetitionObject =
        competitions.find(
            (competition) =>
                String(competition.id) ===
                String(selectedCompetition)
        );

    const selectedSeasonObject =
        seasons.find(
            (season) =>
                String(season.id) ===
                String(selectedSeason)
        );

    const comparisonContext =
        selectedCompetitionObject
            ? selectedSeasonObject
                ? `${selectedCompetitionObject.name} · ${selectedSeasonObject.name}`
                : selectedCompetitionObject.name
            : "Overall Career";

    /* ============================================================
       COMPARISON ROWS
       ============================================================ */

    const battingStats = [
        {
            label: "Matches",
            key: "matches",
            format: formatNumber,
        },
        {
            label: "Runs",
            key: "runs",
            format: formatNumber,
        },
        {
            label: "Highest Score",
            key: "highestScore",
            format: formatNumber,
        },
        {
            label: "Not Outs",
            key: "notOuts",
            format: formatNumber,
        },
        {
            label: "Batting Average",
            key: "battingAverage",
            format: (value) =>
                formatDecimal(value),
        },
        {
            label: "Strike Rate",
            key: "strikeRate",
            format: (value) =>
                formatDecimal(value),
        },
        {
            label: "Fifties",
            key: "fifties",
            format: formatNumber,
        },
        {
            label: "Centuries",
            key: "centuries",
            format: formatNumber,
        },
    ];

    const bowlingStats = [
        {
            label: "Wickets",
            key: "wickets",
            format: formatNumber,
        },
        {
            label: "Runs Conceded",
            key: "runsConceded",
            format: formatNumber,
        },
        {
            label: "Economy",
            key: "economy",
            format: (value) =>
                formatDecimal(value),
        },
        {
            label: "Bowling Average",
            key: "bowlingAverage",
            format: (value) =>
                formatDecimal(value),
        },
        {
            label: "Five-Wicket Hauls",
            key: "fiveWicketHauls",
            format: formatNumber,
        },
    ];

    /* ============================================================
       CHART DATA
       ============================================================ */

    const battingChartData = comparison
        ? [
              {
                  metric: "Runs",
                  player1:
                      playerOne?.runs || 0,
                  player2:
                      playerTwo?.runs || 0,
              },
              {
                  metric: "50s",
                  player1:
                      playerOne?.fifties || 0,
                  player2:
                      playerTwo?.fifties || 0,
              },
              {
                  metric: "100s",
                  player1:
                      playerOne?.centuries || 0,
                  player2:
                      playerTwo?.centuries || 0,
              },
              {
                  metric: "Highest",
                  player1:
                      playerOne?.highestScore || 0,
                  player2:
                      playerTwo?.highestScore || 0,
              },
          ]
        : [];

    const bowlingChartData = comparison
        ? [
              {
                  metric: "Wickets",
                  player1:
                      playerOne?.wickets || 0,
                  player2:
                      playerTwo?.wickets || 0,
              },
              {
                  metric: "5W",
                  player1:
                      playerOne?.fiveWicketHauls ||
                      0,
                  player2:
                      playerTwo?.fiveWicketHauls ||
                      0,
              },
          ]
        : [];

    /* ============================================================
       LOADING
       ============================================================ */

    if (loadingPlayers || loadingFilters) {
        return (
            <div className="page-container">
                <div className="loading-state">
                    Loading comparison data...
                </div>
            </div>
        );
    }

    /* ============================================================
       RENDER
       ============================================================ */

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
                        Player Comparison
                    </h1>

                    <p>
                        Compare two cricketers
                        side by side across
                        key performance metrics.
                    </p>
                </div>
            </div>

            {/* =====================================================
                FILTERS
            ===================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>
                            Comparison Filters
                        </h2>

                        <p>
                            Compare players across
                            different competitions
                            and seasons.
                        </p>
                    </div>
                </div>

                <div className="comparison-filter-grid">

                    {/* COMPETITION */}

                    <div className="comparison-selector">
                        <label htmlFor="competition-filter">
                            Competition
                        </label>

                        <select
                            id="competition-filter"
                            value={
                                selectedCompetition
                            }
                            onChange={
                                handleCompetitionChange
                            }
                            className="filter-select"
                        >
                            <option value="">
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
                                        {
                                            competition.name
                                        }
                                    </option>
                                )
                            )}
                        </select>
                    </div>

                    {/* SEASON */}

                    <div className="comparison-selector">
                        <label htmlFor="season-filter">
                            Season
                        </label>

                        <select
                            id="season-filter"
                            value={
                                selectedSeason
                            }
                            onChange={
                                handleSeasonChange
                            }
                            className="filter-select"
                            disabled={
                                !selectedCompetition
                            }
                        >
                            <option value="">
                                {selectedCompetition
                                    ? "Overall Competition"
                                    : "Select Competition First"}
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

                {/* CURRENT CONTEXT */}

                <div className="comparison-context">
                    <strong>
                        Viewing:
                    </strong>{" "}
                    {comparisonContext}
                </div>

            </section>

            {/* =====================================================
                SELECT PLAYERS
            ===================================================== */}

            <section className="content-section">

                <div className="section-header">
                    <div>
                        <h2>
                            Select Players
                        </h2>

                        <p>
                            Choose two players
                            to compare their
                            statistics.
                        </p>
                    </div>
                </div>

                <div className="comparison-selector-grid">

                    {/* PLAYER 1 */}

                    <div className="comparison-selector">
                        <label htmlFor="player-one">
                            Player 1
                        </label>

                        <select
                            id="player-one"
                            value={
                                selectedPlayer1
                            }
                            onChange={(event) =>
                                setSelectedPlayer1(
                                    event.target.value
                                )
                            }
                            className="filter-select"
                        >
                            <option value="">
                                Select Player
                            </option>

                            {players.map(
                                (player) => (
                                    <option
                                        key={
                                            player.id
                                        }
                                        value={
                                            player.id
                                        }
                                    >
                                        {player.name}
                                        {player.teamName
                                            ? ` · ${player.teamName}`
                                            : ""}
                                    </option>
                                )
                            )}
                        </select>
                    </div>

                    {/* VS */}

                    <div className="comparison-vs">
                        <span>VS</span>
                    </div>

                    {/* PLAYER 2 */}

                    <div className="comparison-selector">
                        <label htmlFor="player-two">
                            Player 2
                        </label>

                        <select
                            id="player-two"
                            value={
                                selectedPlayer2
                            }
                            onChange={(event) =>
                                setSelectedPlayer2(
                                    event.target.value
                                )
                            }
                            className="filter-select"
                        >
                            <option value="">
                                Select Player
                            </option>

                            {players.map(
                                (player) => (
                                    <option
                                        key={
                                            player.id
                                        }
                                        value={
                                            player.id
                                        }
                                    >
                                        {player.name}
                                        {player.teamName
                                            ? ` · ${player.teamName}`
                                            : ""}
                                    </option>
                                )
                            )}
                        </select>
                    </div>

                </div>

                <div className="comparison-action">

                    <button
                        type="button"
                        className="primary-button"
                        onClick={
                            comparePlayers
                        }
                        disabled={
                            loadingComparison ||
                            !selectedPlayer1 ||
                            !selectedPlayer2
                        }
                    >
                        {loadingComparison
                            ? "Comparing..."
                            : "Compare Players"}
                    </button>

                </div>

                {error && (
                    <div className="error-state">
                        {error}
                    </div>
                )}

            </section>

            {/* =====================================================
                COMPARISON RESULT
            ===================================================== */}

            {comparison &&
                playerOne &&
                playerTwo && (
                    <>

                        {/* =================================================
                            PLAYER HEADERS
                        ================================================= */}

                        <section className="comparison-players-grid">

                            <div className="comparison-player-card">

                                <div className="comparison-avatar">
                                    {playerOne.playerName
                                        ?.charAt(0)
                                        ?.toUpperCase()}
                                </div>

                                <div>

                                    <span className="comparison-role">
                                        {playerOne.role ||
                                            "CRICKETER"}
                                    </span>

                                    <h2>
                                        {
                                            playerOne.playerName
                                        }
                                    </h2>

                                    <p>
                                        {playerOne.teamShortName
                                            ? `${playerOne.teamShortName} · ${playerOne.teamName}`
                                            : playerOne.teamName ||
                                              "-"}
                                    </p>

                                </div>

                            </div>

                            <div className="comparison-player-card">

                                <div className="comparison-avatar">
                                    {playerTwo.playerName
                                        ?.charAt(0)
                                        ?.toUpperCase()}
                                </div>

                                <div>

                                    <span className="comparison-role">
                                        {playerTwo.role ||
                                            "CRICKETER"}
                                    </span>

                                    <h2>
                                        {
                                            playerTwo.playerName
                                        }
                                    </h2>

                                    <p>
                                        {playerTwo.teamShortName
                                            ? `${playerTwo.teamShortName} · ${playerTwo.teamName}`
                                            : playerTwo.teamName ||
                                              "-"}
                                    </p>

                                </div>

                            </div>

                        </section>

                        {/* =================================================
                            BATTING COMPARISON
                        ================================================= */}

                        <section className="content-section">

                            <div className="section-header">
                                <div>
                                    <h2>
                                        Batting
                                        Comparison
                                    </h2>

                                    <p>
                                        Side-by-side
                                        batting
                                        statistics.
                                    </p>
                                </div>
                            </div>

                            <div className="comparison-table">

                                <div className="comparison-table-header">
                                    <div>
                                        Metric
                                    </div>

                                    <div>
                                        {
                                            playerOne.playerName
                                        }
                                    </div>

                                    <div>
                                        {
                                            playerTwo.playerName
                                        }
                                    </div>
                                </div>

                                {battingStats.map(
                                    (stat) => (
                                        <div
                                            className="comparison-table-row"
                                            key={
                                                stat.key
                                            }
                                        >
                                            <div className="comparison-metric">
                                                {
                                                    stat.label
                                                }
                                            </div>

                                            <div className="comparison-value">
                                                {stat.format(
                                                    playerOne[
                                                        stat.key
                                                    ]
                                                )}
                                            </div>

                                            <div className="comparison-value">
                                                {stat.format(
                                                    playerTwo[
                                                        stat.key
                                                    ]
                                                )}
                                            </div>
                                        </div>
                                    )
                                )}

                            </div>

                        </section>

                        {/* =================================================
                            BOWLING COMPARISON
                        ================================================= */}

                        <section className="content-section">

                            <div className="section-header">
                                <div>
                                    <h2>
                                        Bowling
                                        Comparison
                                    </h2>

                                    <p>
                                        Side-by-side
                                        bowling
                                        statistics.
                                    </p>
                                </div>
                            </div>

                            <div className="comparison-table">

                                <div className="comparison-table-header">

                                    <div>
                                        Metric
                                    </div>

                                    <div>
                                        {
                                            playerOne.playerName
                                        }
                                    </div>

                                    <div>
                                        {
                                            playerTwo.playerName
                                        }
                                    </div>

                                </div>

                                {bowlingStats.map(
                                    (stat) => (
                                        <div
                                            className="comparison-table-row"
                                            key={
                                                stat.key
                                            }
                                        >

                                            <div className="comparison-metric">
                                                {
                                                    stat.label
                                                }
                                            </div>

                                            <div className="comparison-value">
                                                {stat.format(
                                                    playerOne[
                                                        stat.key
                                                    ]
                                                )}
                                            </div>

                                            <div className="comparison-value">
                                                {stat.format(
                                                    playerTwo[
                                                        stat.key
                                                    ]
                                                )}
                                            </div>

                                        </div>
                                    )
                                )}

                            </div>

                        </section>

                        {/* =================================================
                            BATTING CHART
                        ================================================= */}

                        <section className="content-section">

                            <div className="section-header">
                                <div>
                                    <h2>
                                        Batting
                                        Visual
                                        Comparison
                                    </h2>

                                    <p>
                                        Key batting
                                        milestones
                                        compared
                                        visually.
                                    </p>
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
                                            dataKey="metric"
                                        />

                                        <YAxis />

                                        <Tooltip />

                                        <Bar
                                            dataKey="player1"
                                            name={
                                                playerOne.playerName
                                            }
                                        />

                                        <Bar
                                            dataKey="player2"
                                            name={
                                                playerTwo.playerName
                                            }
                                        />
                                    </BarChart>
                                </ResponsiveContainer>

                            </div>

                        </section>

                        {/* =================================================
                            BOWLING CHART
                        ================================================= */}

                        <section className="content-section">

                            <div className="section-header">
                                <div>
                                    <h2>
                                        Bowling
                                        Visual
                                        Comparison
                                    </h2>

                                    <p>
                                        Wickets and
                                        five-wicket
                                        hauls.
                                    </p>
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
                                            dataKey="metric"
                                        />

                                        <YAxis />

                                        <Tooltip />

                                        <Bar
                                            dataKey="player1"
                                            name={
                                                playerOne.playerName
                                            }
                                        />

                                        <Bar
                                            dataKey="player2"
                                            name={
                                                playerTwo.playerName
                                            }
                                        />

                                    </BarChart>
                                </ResponsiveContainer>

                            </div>

                        </section>

                        {/* =================================================
                            BACK TO PLAYERS
                        ================================================= */}

                        <section className="content-section">

                            <div className="action-grid">

                                <Link
                                    to={`/players/${playerOne.playerId}`}
                                    className="action-card"
                                >
                                    <h3>
                                        View{" "}
                                        {
                                            playerOne.playerName
                                        }
                                    </h3>

                                    <p>
                                        Open the full
                                        player profile.
                                    </p>
                                </Link>

                                <Link
                                    to={`/players/${playerTwo.playerId}`}
                                    className="action-card"
                                >
                                    <h3>
                                        View{" "}
                                        {
                                            playerTwo.playerName
                                        }
                                    </h3>

                                    <p>
                                        Open the full
                                        player profile.
                                    </p>
                                </Link>

                            </div>

                        </section>

                    </>
                )}

        </div>
    );
}

export default PlayerComparison;