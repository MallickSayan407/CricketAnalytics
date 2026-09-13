import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Teams() {
    const [teams, setTeams] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchTeams();
    }, []);

    const fetchTeams = async () => {
        try {
            const response = await api.get("/teams");
            setTeams(response.data);
        } catch (err) {
            console.error("Error fetching teams:", err);
            setError("Unable to load teams.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="page-container">
                <h1>Teams</h1>
                <p>Loading teams...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container">
                <h1>Teams</h1>
                <p className="error-message">{error}</p>
            </div>
        );
    }

    return (
        <div className="page-container">

            <div className="page-header">
                <div>
                    <h1>Teams</h1>
                    <p>Explore team statistics and analytics.</p>
                </div>

                <div className="page-count">
                    {teams.length} Teams
                </div>
            </div>

            {teams.length === 0 ? (
                <div className="empty-state">
                    <h2>No teams found</h2>
                    <p>There are currently no teams available.</p>
                </div>
            ) : (
                <div className="team-grid">

                    {teams.map((team) => (

                        <Link
                            key={team.id}
                            to={`/teams/${team.id}`}
                            className="team-card-link"
                        >

                            <div className="team-card">

                                <div className="team-logo">

                                    {team.logoUrl ? (
                                        <img
                                            src={team.logoUrl}
                                            alt={`${team.name} logo`}
                                        />
                                    ) : (
                                        <span>
                                            {team.shortName?.substring(0, 3)}
                                        </span>
                                    )}

                                </div>

                                <div className="team-info">

                                    <h2>{team.name}</h2>

                                    <span className="team-short-name">
                                        {team.shortName}
                                    </span>

                                    <p>{team.country}</p>

                                </div>

                                <div className="team-arrow">
                                    →
                                </div>

                            </div>

                        </Link>

                    ))}

                </div>
            )}

        </div>
    );
}

export default Teams;