function StatCard({ label, value, description }) {
    return (
        <div className="stat-card">

            <span className="stat-label">
                {label}
            </span>

            <span className="stat-value">
                {value}
            </span>

            {description && (
                <span className="stat-description">
                    {description}
                </span>
            )}

        </div>
    );
}

export default StatCard;