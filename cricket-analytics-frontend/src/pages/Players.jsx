import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../services/api";

function Players() {

    const [players, setPlayers] = useState([]);

    const [searchTerm, setSearchTerm] = useState("");

    const [loading, setLoading] = useState(true);

    const [error, setError] = useState("");


    useEffect(() => {

        const fetchPlayers = async () => {

            try {

                setLoading(true);
                setError("");

                const response = await api.get("/players");

                setPlayers(
                    Array.isArray(response.data)
                        ? response.data
                        : []
                );

            } catch (err) {

                console.error(
                    "Failed to load players:",
                    err
                );

                setError(
                    "Unable to load players from the backend."
                );

            } finally {

                setLoading(false);

            }

        };

        fetchPlayers();

    }, []);


    const filteredPlayers = players.filter((player) => {

        const search = searchTerm
            .toLowerCase()
            .trim();

        if (!search) {
            return true;
        }

        return (
            player.name?.toLowerCase().includes(search) ||
            player.role?.toLowerCase().includes(search) ||
            player.battingStyle?.toLowerCase().includes(search) ||
            player.bowlingStyle?.toLowerCase().includes(search) ||
            player.teamName?.toLowerCase().includes(search)
        );

    });


    return (

        <main className="page-container">

            {/* Header */}

            <section className="page-header">

                <div>

                    <p className="eyebrow">
                        CRICKET DATABASE
                    </p>

                    <h1>
                        Players
                    </h1>

                    <p className="page-description">
                        Explore players, roles and playing styles.
                    </p>

                </div>

            </section>


            {/* Search */}

            <section className="search-section">

                <input
                    type="text"
                    placeholder="Search player, role or playing style..."
                    value={searchTerm}
                    onChange={(event) =>
                        setSearchTerm(event.target.value)
                    }
                    className="player-search"
                />

                <span className="result-count">
                    {filteredPlayers.length} player
                    {filteredPlayers.length !== 1 ? "s" : ""}
                </span>

            </section>


            {/* Loading */}

            {loading && (

                <div className="status-message">
                    Loading players...
                </div>

            )}


            {/* Error */}

            {!loading && error && (

                <div className="status-message error">
                    {error}
                </div>

            )}


            {/* Empty */}

            {!loading &&
                !error &&
                filteredPlayers.length === 0 && (

                    <div className="status-message">

                        No players found.

                    </div>

                )}


            {/* Player Cards */}

            {!loading &&
                !error &&
                filteredPlayers.length > 0 && (

                    <section className="players-grid">

                        {filteredPlayers.map((player) => (

                            <article
                                className="player-card"
                                key={player.id}
                            >

                                <div className="player-avatar">

                                    {player.avatarUrl ? (

                                        <img
                                            src={player.avatarUrl}
                                            alt={player.name}
                                        />

                                    ) : (

                                        <span>
                                            {player.name
                                                ?.charAt(0)
                                                .toUpperCase()}
                                        </span>

                                    )}

                                </div>


                                <div className="player-card-content">

                                    <p className="player-role">
                                        {player.role}
                                    </p>

                                    <h2>
                                        {player.name}
                                    </h2>


                                    <div className="player-details">

                                        <div>
                                            <span>
                                                Team
                                            </span>

                                            <strong>
                                                {player.teamName ||
                                                    "Not assigned"}
                                            </strong>
                                        </div>


                                        <div>
                                            <span>
                                                Batting
                                            </span>

                                            <strong>
                                                {player.battingStyle ||
                                                    "Not available"}
                                            </strong>
                                        </div>


                                        <div>
                                            <span>
                                                Bowling
                                            </span>

                                            <strong>
                                                {player.bowlingStyle ||
                                                    "Not available"}
                                            </strong>
                                        </div>

                                    </div>


                                    <Link
                                        to={`/players/${player.id}`}
                                        className="profile-link"
                                    >
                                        View Profile →
                                    </Link>

                                </div>

                            </article>

                        ))}

                    </section>

                )}

        </main>

    );
}

export default Players;