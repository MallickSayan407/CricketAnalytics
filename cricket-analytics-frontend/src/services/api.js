import axios from "axios";

const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

export const getTeams = () => {
    return api.get("/teams");
};

export const getVenues = () => {
    return api.get("/venues");
};

export const predictODI = (data) => {
    return api.post("/ml/predict/odi", data);
};

export const simulateTournament = (data, simulations = 10000) => {
    return api.post(
        `/simulator/odi/monte-carlo?simulations=${simulations}`,
        data
    );
};


export const simulateSingleTournament = (
    request
) => {

    return api.post(
        "/simulator/odi/tournament",
        request
    );
};
export default api;