import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Seasons() {
    const [seasons, setSeasons] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchSeasons();
    }, []);

    const fetchSeasons = async () => {
        try {
            const response = await api.get("/seasons");
            setSeasons(response.data);
        } catch (err) {
            console.error("Error fetching seasons:", err);
            setError("Unable to load seasons.");
        } finally {
            setLoading(false);
        }
    };

    const getCompetitionName = (season) => {
        if (season.competition) {
            if (typeof season.competition === "object") {
                return season.competition.name || "Competition";
            }

            return season.competition;
        }

        return season.competitionName || "Competition";
    };

    const getCompetitionType = (season) => {
        if (
            season.competition &&
            typeof season.competition === "object"
        ) {
            return season.competition.type || "";
        }

        return season.competitionType || "";
    };

    const getCompetitionFormat = (season) => {
        if (
            season.competition &&
            typeof season.competition === "object"
        ) {
            return season.competition.format || "";
        }

        return season.format || season.competitionFormat || "";
    };

    if (loading) {
        return (
            <div className="page-container">
                <h1>Seasons</h1>
                <p>Loading seasons...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container">
                <h1>Seasons</h1>
                <p className="error-message">{error}</p>
            </div>
        );
    }

    return (
        <div className="page-container">

            <div className="page-header">
                <div>
                    <h1>Seasons</h1>
                    <p>
                        Explore competition seasons and performance.
                    </p>
                </div>

                <div className="page-count">
                    {seasons.length} Seasons
                </div>
            </div>

            {seasons.length === 0 ? (
                <div className="empty-state">
                    <h2>No seasons found</h2>
                    <p>
                        There are currently no seasons available.
                    </p>
                </div>
            ) : (
                <div className="season-grid">

                    {seasons.map((season) => {

                        const competitionName =
                            getCompetitionName(season);

                        const competitionType =
                            getCompetitionType(season);

                        const competitionFormat =
                            getCompetitionFormat(season);

                        return (
                            <Link
                                key={season.id}
                                to={`/seasons/${season.id}`}
                                className="season-card-link"
                            >

                                <div className="season-card">

                                    <div className="season-icon">
                                        {competitionType === "IPL"
                                            ? "🏆"
                                            : "🏏"}
                                    </div>

                                    <div className="season-info">

                                        <span className="season-type">
                                            {competitionType ||
                                                "CRICKET"}
                                        </span>

                                        <h2>
                                            {competitionName}
                                        </h2>

                                        <div className="season-meta">

                                            <span>
                                                {season.name}
                                            </span>

                                            {competitionFormat && (
                                                <span>
                                                    {competitionFormat}
                                                </span>
                                            )}

                                        </div>

                                        {season.startYear && (
                                            <p>
                                                {season.startYear}
                                                {season.endYear &&
                                                    season.endYear !==
                                                        season.startYear
                                                    ? ` - ${season.endYear}`
                                                    : ""}
                                            </p>
                                        )}

                                    </div>

                                    <div className="season-arrow">
                                        →
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

export default Seasons;