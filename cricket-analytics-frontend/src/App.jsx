import {
    BrowserRouter,
    Routes,
    Route,
    Link
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import Players from "./pages/Players";
import PlayerProfile from "./pages/PlayerProfile";
import PlayerComparison from "./pages/PlayerComparison";
import MatchDetails from "./pages/MatchDetails";
import Teams from "./pages/Teams";
import TeamProfile from "./pages/TeamProfile";
import Predictor from "./pages/Predictor";
import Matches from "./pages/Matches";
import MatchAnalytics from "./pages/MatchAnalytics";
import PlayerTrends from "./pages/PlayerTrends";
import Venues from "./pages/Venues";
import VenueAnalytics from "./pages/VenueAnalytics";
import TournamentSimulator from "./pages/TournamentSimulator";
import Seasons from "./pages/Seasons";
import SeasonAnalytics from "./pages/SeasonAnalytics";

import Leaderboards from "./pages/Leaderboards";

import "./App.css";


function App() {

    return (

        <BrowserRouter>

            <div className="app">

                {/* =====================================================
                    NAVBAR
                ===================================================== */}

                <header className="navbar">

                    <Link
                        to="/"
                        className="brand"
                    >
                        🏏 Cricket Analytics
                    </Link>


                    <nav className="nav-links">

                        <Link to="/">
                            Dashboard
                        </Link>

                        <Link to="/players">
                            Players
                        </Link>

                        <Link to="/teams">
                            Teams
                        </Link>

                        <Link to="/player-comparison">
                            Compare
                        </Link>

                        <Link to="/venues">
                            Venues
                        </Link>

                        <Link to="/matches">
                            Matches
                        </Link>

                        <Link to="/seasons">
                            Seasons
                        </Link>

                        <Link to="/leaderboards">
                            Leaderboards
                        </Link>
						
						<Link to="/predictor">
						    Predictor
						</Link>
						
						<Link to="/tournament-simulator">
						    Tournament Simulator
						</Link>

                    </nav>

                </header>


                {/* =====================================================
                    ROUTES
                ===================================================== */}

                <Routes>

                    {/* =================================================
                        DASHBOARD
                    ================================================= */}

                    <Route
                        path="/"
                        element={<Dashboard />}
                    />


                    {/* =================================================
                        PLAYERS
                    ================================================= */}

                    <Route
                        path="/players"
                        element={<Players />}
                    />

                    <Route
                        path="/players/:playerId"
                        element={<PlayerProfile />}
                    />

                    {/* IMPORTANT:
                        This is the route used by the
                        "Compare Player" button on PlayerProfile.
                    */}

                    <Route
                        path="/players/:playerId/comparison"
                        element={<PlayerComparison />}
                    />

					<Route
					    path="/players/:playerId/trends"
					    element={<PlayerTrends />}
					/>

                    {/* =================================================
                        PLAYER COMPARISON
                    ================================================= */}

                    {/* Navbar → Compare */}

                    <Route
                        path="/player-comparison"
                        element={<PlayerComparison />}
                    />


					
                    {/* =================================================
                        TEAMS
                    ================================================= */}

                    <Route
                        path="/teams"
                        element={<Teams />}
                    />

					<Route
					    path="/teams/:teamId"
					    element={<TeamProfile />}
					/>


                    {/* =================================================
                        MATCHES
                    ================================================= */}

                    <Route
                        path="/matches"
                        element={<Matches />}
                    />

                    <Route
                        path="/matches/:matchId"
                        element={<MatchAnalytics />}
                    />

					<Route
					    path="/matches/:matchId"
					    element={<MatchDetails />}
					/>

                    {/* =================================================
                        VENUES
                    ================================================= */}

                    <Route
                        path="/venues"
                        element={<Venues />}
                    />

                    <Route
                        path="/venues/:venueId"
                        element={<VenueAnalytics />}
                    />


                    {/* =================================================
                        SEASONS
                    ================================================= */}

                    <Route
                        path="/seasons"
                        element={<Seasons />}
                    />

                    <Route
                        path="/seasons/:seasonId"
                        element={<SeasonAnalytics />}
                    />


                    {/* =================================================
                        LEADERBOARDS
                    ================================================= */}

                    <Route
                        path="/leaderboards"
                        element={<Leaderboards />}
                    />
					
					{/*===================================================
						PREDICTOR
					  ===================================================*/}
					
					<Route
					    path="/predictor"
					    element={<Predictor />}
					/>
					
					{/*===================================================
						TOURNAMENT SIMULATOR
					  ===================================================*/}
					
					<Route
					    path="/tournament-simulator"
					    element={<TournamentSimulator />}
					/>

                </Routes>

            </div>

        </BrowserRouter>

    );
}

export default App;