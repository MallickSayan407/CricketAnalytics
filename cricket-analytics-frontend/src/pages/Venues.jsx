import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function Venues() {
    const [venues, setVenues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        fetchVenues();
    }, []);

    const fetchVenues = async () => {
        try {
            const response = await api.get("/venues");
            setVenues(response.data);
        } catch (err) {
            console.error("Error fetching venues:", err);
            setError("Unable to load venues.");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="page-container">
                <h1>Venues</h1>
                <p>Loading venues...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page-container">
                <h1>Venues</h1>
                <p className="error-message">{error}</p>
            </div>
        );
    }

    return (
        <div className="page-container">

            <div className="page-header">
                <div>
                    <h1>Venues</h1>
                    <p>
                        Explore cricket grounds and venue performance.
                    </p>
                </div>

                <div className="page-count">
                    {venues.length} Venues
                </div>
            </div>

            {venues.length === 0 ? (
                <div className="empty-state">
                    <h2>No venues found</h2>
                    <p>
                        There are currently no venues available.
                    </p>
                </div>
            ) : (
                <div className="venue-grid">

                    {venues.map((venue) => (

                        <Link
                            key={venue.id}
                            to={`/venues/${venue.id}`}
                            className="venue-card-link"
                        >

                            <div className="venue-card">

                                <div className="venue-icon">
                                    🏟️
                                </div>

                                <div className="venue-info">

                                    <h2>{venue.name}</h2>

                                    <p>
                                        {venue.city}
                                        {venue.country &&
                                            `, ${venue.country}`}
                                    </p>

                                    {venue.capacity && (
                                        <span className="venue-capacity">
                                            Capacity:{" "}
                                            {venue.capacity.toLocaleString()}
                                        </span>
                                    )}

                                </div>

                                <div className="venue-arrow">
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

export default Venues;