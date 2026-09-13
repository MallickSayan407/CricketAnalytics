import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Matches() {
    const [matches, setMatches] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchMatches();
    }, []);

    const fetchMatches = async () => {
        try {
            const response = await api.get("/matches");
            setMatches(response.data);
        } catch (err) {
            console.error("Error fetching matches:", err);
            setError("Unable to load matches.");
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

    const getTeamName = (match, teamNumber) => {
        const team = match[`team${teamNumber}`];

        if (team && typeof team === "object") {
            return team.name || team.teamName || "Unknown Team";
        }

        return (
            match[`team${teamNumber}Name`] ||
            match[`team${teamNumber}`] ||
            "Unknown Team"
        );
    };

    const getTeamShortName = (match, teamNumber) => {
        const team = match[`team${teamNumber}`];

        if (team && typeof team === "object") {
            return team.shortName || team.teamShortName || "";
        }

        return match[`team${teamNumber}ShortName`] || "";
    };

    const getWinnerName = (match) => {
        if (match.winner && typeof match.winner === "object") {
            return match.winner.name || match.winner.teamName || "";
        }

        return match.winner || "";
    };

    if (loading) {
        return (
            <div className="page-container">
                <h1>Matches</h1>
                <p>Loading matches...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container">
                <h1>Matches</h1>
                <p className="error-message">{error}</p>
            </div>
        );
    }

    return (
        <div className="page-container">

            <div className="page-header">
                <div>
                    <h1>Matches</h1>
                    <p>Explore cricket matches and scorecards.</p>
                </div>

                <div className="page-count">
                    {matches.length} Matches
                </div>
            </div>

            {matches.length === 0 ? (
                <div className="empty-state">
                    <h2>No matches found</h2>
                    <p>There are currently no matches available.</p>
                </div>
            ) : (
                <div className="matches-list">

                    {matches.map((match) => {
                        const team1Name = getTeamName(match, 1);
                        const team2Name = getTeamName(match, 2);

                        const team1ShortName =
                            getTeamShortName(match, 1);

                        const team2ShortName =
                            getTeamShortName(match, 2);

                        const winnerName = getWinnerName(match);

                        return (
                            <Link
                                key={match.id}
                                to={`/matches/${match.id}`}
                                className="match-card-link"
                            >

                                <div className="match-card">

                                    <div className="match-card-top">

                                        <div>
                                            <span className="match-competition">
                                                {match.competitionName ||
                                                    "Cricket Match"}
                                            </span>

                                            {match.competitionFormat && (
                                                <span className="match-format">
                                                    {match.competitionFormat}
                                                </span>
                                            )}
                                        </div>

                                        <span
                                            className={`match-status ${
                                                match.matchStatus ===
                                                "COMPLETED"
                                                    ? "completed"
                                                    : ""
                                            }`}
                                        >
                                            {match.matchStatus ||
                                                "UNKNOWN"}
                                        </span>

                                    </div>

                                    <div className="match-teams">

                                        <div className="match-team">

                                            <div className="match-team-badge">
                                                {team1ShortName ||
                                                    team1Name
                                                        .substring(0, 3)
                                                        .toUpperCase()}
                                            </div>

                                            <div className="match-team-details">
                                                <h2>{team1Name}</h2>

                                                {match.team1Score && (
                                                    <span>
                                                        {match.team1Score}
                                                    </span>
                                                )}
                                            </div>

                                        </div>

                                        <div className="match-vs">
                                            VS
                                        </div>

                                        <div className="match-team">

                                            <div className="match-team-badge">
                                                {team2ShortName ||
                                                    team2Name
                                                        .substring(0, 3)
                                                        .toUpperCase()}
                                            </div>

                                            <div className="match-team-details">
                                                <h2>{team2Name}</h2>

                                                {match.team2Score && (
                                                    <span>
                                                        {match.team2Score}
                                                    </span>
                                                )}
                                            </div>

                                        </div>

                                    </div>

                                    <div className="match-card-bottom">

                                        <div className="match-date">
                                            {formatDate(match.matchDate)}
                                        </div>

                                        <div className="match-venue">
                                            {match.venueName ||
                                                "Venue unavailable"}

                                            {match.venueCity &&
                                                `, ${match.venueCity}`}
                                        </div>

                                        {winnerName && (
                                            <div className="match-winner">
                                                Winner: {winnerName}
                                            </div>
                                        )}

                                        <div className="match-arrow">
                                            →
                                        </div>

                                    </div>

                                </div>

                            </Link>
                        );
                    })}

                </div>
            )}

        </div>
    );
}

export default Matches;