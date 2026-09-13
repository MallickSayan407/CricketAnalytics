import { useEffect, useMemo, useState } from "react";
import api from "../services/api";

const leaderboardTypes = [
    {
        key: "runs",
        label: "Runs",
        endpoint: "/analytics/leaderboard/runs",
        valueField: "runs",
        valueLabel: "Runs",
        format: (value) => value?.toLocaleString() ?? "0",
    },
    {
        key: "batting-average",
        label: "Batting Average",
        endpoint: "/analytics/leaderboard/batting-average",
        valueField: "battingAverage",
        valueLabel: "Average",
        format: (value) => Number(value ?? 0).toFixed(2),
    },
    {
        key: "strike-rate",
        label: "Strike Rate",
        endpoint: "/analytics/leaderboard/strike-rate",
        valueField: "strikeRate",
        valueLabel: "Strike Rate",
        format: (value) => Number(value ?? 0).toFixed(2),
    },
    {
        key: "centuries",
        label: "Centuries",
        endpoint: "/analytics/leaderboard/centuries",
        valueField: "centuries",
        valueLabel: "Centuries",
        format: (value) => value ?? 0,
    },
    {
        key: "wickets",
        label: "Wickets",
        endpoint: "/analytics/leaderboard/wickets",
        valueField: "wickets",
        valueLabel: "Wickets",
        format: (value) => value ?? 0,
    },
];

function Leaderboards() {
    const [competitions, setCompetitions] = useState([]);
    const [seasons, setSeasons] = useState([]);

    const [selectedCompetition, setSelectedCompetition] = useState("");
    const [selectedSeason, setSelectedSeason] = useState("");

    const [activeType, setActiveType] = useState("runs");
    const [leaderboard, setLeaderboard] = useState([]);

    const [loadingFilters, setLoadingFilters] = useState(true);
    const [loadingLeaderboard, setLoadingLeaderboard] = useState(false);
    const [error, setError] = useState("");

    // --------------------------------------------------
    // Load competitions and seasons
    // --------------------------------------------------

    useEffect(() => {
        const loadFilters = async () => {
            try {
                setLoadingFilters(true);
                setError("");

                const [competitionResponse, seasonResponse] =
                    await Promise.all([
                        api.get("/competitions"),
                        api.get("/seasons"),
                    ]);

                setCompetitions(competitionResponse.data || []);
                setSeasons(seasonResponse.data || []);
            } catch (err) {
                console.error("Failed to load leaderboard filters:", err);
                setError("Failed to load competition and season filters.");
            } finally {
                setLoadingFilters(false);
            }
        };

        loadFilters();
    }, []);

    // --------------------------------------------------
    // Filter seasons according to selected competition
    // --------------------------------------------------

    const filteredSeasons = useMemo(() => {
        if (!selectedCompetition) {
            return [];
        }

        return seasons.filter(
            (season) =>
                String(season.competitionId) === String(selectedCompetition)
        );
    }, [seasons, selectedCompetition]);

    // --------------------------------------------------
    // Load leaderboard
    // --------------------------------------------------

    useEffect(() => {
        const loadLeaderboard = async () => {
            const selectedType = leaderboardTypes.find(
                (type) => type.key === activeType
            );

            if (!selectedType) {
                return;
            }

            try {
                setLoadingLeaderboard(true);
                setError("");

                const params = new URLSearchParams();

                if (selectedCompetition) {
                    params.append("competitionId", selectedCompetition);
                }

                if (selectedSeason) {
                    params.append("seasonId", selectedSeason);
                }

                const queryString = params.toString();

                const url = queryString
                    ? `${selectedType.endpoint}?${queryString}`
                    : selectedType.endpoint;

                const response = await api.get(url);

                setLeaderboard(response.data || []);
            } catch (err) {
                console.error("Failed to load leaderboard:", err);

                setLeaderboard([]);
                setError("Failed to load leaderboard data.");
            } finally {
                setLoadingLeaderboard(false);
            }
        };

        if (!loadingFilters) {
            loadLeaderboard();
        }
    }, [
        activeType,
        selectedCompetition,
        selectedSeason,
        loadingFilters,
    ]);

    // --------------------------------------------------
    // Competition change
    // --------------------------------------------------

    const handleCompetitionChange = (event) => {
        const value = event.target.value;

        setSelectedCompetition(value);
        setSelectedSeason("");
        setLeaderboard([]);
    };

    // --------------------------------------------------
    // Season change
    // --------------------------------------------------

    const handleSeasonChange = (event) => {
        setSelectedSeason(event.target.value);
    };

    // --------------------------------------------------
    // Context label
    // --------------------------------------------------

    const selectedCompetitionObject = competitions.find(
        (competition) =>
            String(competition.id) === String(selectedCompetition)
    );

    const selectedSeasonObject = seasons.find(
        (season) => String(season.id) === String(selectedSeason)
    );

    const contextLabel = !selectedCompetition
        ? "Overall Career"
        : selectedSeason
            ? `${selectedCompetitionObject?.name || "Competition"} · ${
                  selectedSeasonObject?.name || "Season"
              }`
            : selectedCompetitionObject?.name || "Competition";

    const activeLeaderboardType = leaderboardTypes.find(
        (type) => type.key === activeType
    );

    return (
        <div className="page-container leaderboard-page">

            {/* --------------------------------------------------
                Header
            -------------------------------------------------- */}

            <div className="page-header leaderboard-header">
                <div>
                    <h1># Leaderboards</h1>
                    <p>
                        Explore the leading performers across international
                        cricket and IPL.
                    </p>
                </div>
            </div>

            {/* --------------------------------------------------
                Filters
            -------------------------------------------------- */}

            <div className="leaderboard-filter-card">

                <div className="leaderboard-filter-group">
                    <label htmlFor="leaderboard-competition">
                        Competition
                    </label>

                    <select
                        id="leaderboard-competition"
                        value={selectedCompetition}
                        onChange={handleCompetitionChange}
                        disabled={loadingFilters}
                    >
                        <option value="">
                            Overall Career
                        </option>

                        {competitions.map((competition) => (
                            <option
                                key={competition.id}
                                value={competition.id}
                            >
                                {competition.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="leaderboard-filter-group">
                    <label htmlFor="leaderboard-season">
                        Season
                    </label>

                    <select
                        id="leaderboard-season"
                        value={selectedSeason}
                        onChange={handleSeasonChange}
                        disabled={
                            loadingFilters ||
                            !selectedCompetition ||
                            filteredSeasons.length === 0
                        }
                    >
                        <option value="">
                            All Seasons
                        </option>

                        {filteredSeasons.map((season) => (
                            <option
                                key={season.id}
                                value={season.id}
                            >
                                {season.name}
                            </option>
                        ))}
                    </select>
                </div>

            </div>

            {/* --------------------------------------------------
                Context
            -------------------------------------------------- */}

            <div className="leaderboard-context">
                Showing: <strong>{contextLabel}</strong>
            </div>

            {/* --------------------------------------------------
                Leaderboard Tabs
            -------------------------------------------------- */}

            <div className="leaderboard-tabs">

                {leaderboardTypes.map((type) => (
                    <button
                        key={type.key}
                        className={
                            activeType === type.key
                                ? "leaderboard-tab active"
                                : "leaderboard-tab"
                        }
                        onClick={() => setActiveType(type.key)}
                    >
                        {type.label}
                    </button>
                ))}

            </div>

            {/* --------------------------------------------------
                Leaderboard Content
            -------------------------------------------------- */}

            <section className="leaderboard-section">

                <div className="leaderboard-section-header">
                    <div>
                        <h2>
                            Top {activeLeaderboardType?.label}
                        </h2>

                        <p>
                            Ranked by {activeLeaderboardType?.valueLabel}.
                        </p>
                    </div>

                    {!loadingLeaderboard && leaderboard.length > 0 && (
                        <span className="leaderboard-count">
                            {leaderboard.length} players
                        </span>
                    )}
                </div>

                {error && (
                    <div className="leaderboard-error">
                        {error}
                    </div>
                )}

                {loadingLeaderboard ? (
                    <div className="leaderboard-loading">
                        <div className="loading-spinner"></div>
                        <p>Loading leaderboard...</p>
                    </div>
                ) : leaderboard.length === 0 ? (
                    <div className="leaderboard-empty">
                        <h3>No leaderboard data</h3>
                        <p>
                            There are no player records available for the
                            selected filters.
                        </p>
                    </div>
                ) : (
                    <div className="leaderboard-table-wrapper">

                        <table className="leaderboard-table">

                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Player</th>
                                    <th>Team</th>
                                    <th>Matches</th>
                                    <th>
                                        {activeLeaderboardType?.valueLabel}
                                    </th>
                                    <th>Average</th>
                                    <th>Strike Rate</th>
                                    <th>100s</th>
                                    <th>50s</th>
                                    <th>Wickets</th>
                                </tr>
                            </thead>

                            <tbody>

                                {leaderboard.map((player, index) => {

                                    const rank =
                                        player.rank ?? index + 1;

                                    const value =
                                        player[
                                            activeLeaderboardType.valueField
                                        ];

                                    return (
                                        <tr key={player.playerId}>

                                            <td>
                                                <span
                                                    className={
                                                        rank <= 3
                                                            ? `leaderboard-rank rank-${rank}`
                                                            : "leaderboard-rank"
                                                    }
                                                >
                                                    {rank}
                                                </span>
                                            </td>

                                            <td>
                                                <div className="leaderboard-player">

                                                    <div className="leaderboard-avatar">
                                                        {player.playerName
                                                            ?.charAt(0)
                                                            ?.toUpperCase() || "?"}
                                                    </div>

                                                    <div>
                                                        <strong>
                                                            {player.playerName}
                                                        </strong>

                                                        <span>
                                                            {player.playerRole
                                                                ?.replaceAll(
                                                                    "_",
                                                                    " "
                                                                ) || "PLAYER"}
                                                        </span>
                                                    </div>

                                                </div>
                                            </td>

                                            <td>
                                                <div className="leaderboard-team">

                                                    <strong>
                                                        {player.teamShortName ||
                                                            "-"}
                                                    </strong>

                                                    <span>
                                                        {player.teamName || "-"}
                                                    </span>

                                                </div>
                                            </td>

                                            <td>
                                                {player.matches ?? 0}
                                            </td>

                                            <td>
                                                <strong className="leaderboard-primary-value">
                                                    {activeLeaderboardType.format(
                                                        value
                                                    )}
                                                </strong>
                                            </td>

                                            <td>
                                                {Number(
                                                    player.battingAverage ?? 0
                                                ).toFixed(2)}
                                            </td>

                                            <td>
                                                {Number(
                                                    player.strikeRate ?? 0
                                                ).toFixed(2)}
                                            </td>

                                            <td>
                                                {player.centuries ?? 0}
                                            </td>

                                            <td>
                                                {player.fifties ?? 0}
                                            </td>

                                            <td>
                                                {player.wickets ?? 0}
                                            </td>

                                        </tr>
                                    );
                                })}

                            </tbody>

                        </table>

                    </div>
                )}

            </section>

        </div>
    );
}

export default Leaderboards;