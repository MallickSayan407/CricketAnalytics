package com.cricketanalytics.simulator.service;

import com.cricketanalytics.ml.dto.ODIPredictionRequest;
import com.cricketanalytics.ml.dto.ODIPredictionResponse;
import com.cricketanalytics.ml.service.MLPredictionService;
import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODIFixtureResponse;
import com.cricketanalytics.simulator.dto.ODIMonteCarloResult;
import com.cricketanalytics.simulator.dto.ODIMonteCarloTeamResult;
import com.cricketanalytics.simulator.dto.ODITeamStanding;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class ODIMonteCarloSimulationService {

    private final ODISimulatorService fixtureService;
    private final MLPredictionService mlPredictionService;

    public ODIMonteCarloSimulationService(
            ODISimulatorService fixtureService,
            MLPredictionService mlPredictionService
    ) {
        this.fixtureService = fixtureService;
        this.mlPredictionService = mlPredictionService;
    }

    public ODIMonteCarloResult simulate(
            ODIFixtureRequest request,
            int simulations
    ) {

        if (simulations <= 0) {
            throw new IllegalArgumentException(
                    "Simulations must be greater than 0"
            );
        }

        if (simulations > 10000) {
            throw new IllegalArgumentException(
                    "Maximum simulations allowed is 10000"
            );
        }

        // --------------------------------------------------
        // 1. Generate league fixtures
        // --------------------------------------------------

        List<ODIFixtureResponse> fixtures =
                fixtureService.generateFixtures(request);

        // --------------------------------------------------
        // 2. Build probability cache
        // --------------------------------------------------

        Map<String, ODIMatchProbability> probabilityCache =
                buildProbabilityCache(
                        fixtures,
                        request.predictionDate()
                );

        // --------------------------------------------------
        // 3. Initialize counters
        // --------------------------------------------------

        Map<String, Integer> championshipWins =
                new LinkedHashMap<>();

        Map<String, Integer> qualificationCounts =
                new LinkedHashMap<>();
        
        Map<String, Integer> finalAppearances =
                new LinkedHashMap<>();

        Map<String, Integer> firstPlaceCounts =
                new LinkedHashMap<>();

        Map<String, Integer> secondPlaceCounts =
                new LinkedHashMap<>();

        Map<String, Integer> thirdPlaceCounts =
                new LinkedHashMap<>();

        Map<String, Integer> fourthPlaceCounts =
                new LinkedHashMap<>();

        for (String team : request.teams()) {

            championshipWins.put(
                    team,
                    0
            );

            qualificationCounts.put(
                    team,
                    0
            );

            finalAppearances.put(
                    team,
                    0
            );

            firstPlaceCounts.put(
                    team,
                    0
            );

            secondPlaceCounts.put(
                    team,
                    0
            );

            thirdPlaceCounts.put(
                    team,
                    0
            );

            fourthPlaceCounts.put(
                    team,
                    0
            );
        }

        // --------------------------------------------------
        // 4. Monte Carlo simulations
        // --------------------------------------------------

        for (int simulation = 0;
             simulation < simulations;
             simulation++) {

            List<ODITeamStanding> standings =
                    simulateLeague(
                            request.teams(),
                            fixtures,
                            probabilityCache
                    );

            // --------------------------------------------------
            // Top four qualify
            // --------------------------------------------------

            for (int i = 0; i < 4; i++) {

                String qualifiedTeam =
                        standings.get(i).team();

                qualificationCounts.merge(
                        qualifiedTeam,
                        1,
                        Integer::sum
                );
            }

            // --------------------------------------------------
            // Top four
            // --------------------------------------------------

            String first =
                    standings.get(0).team();

            String second =
                    standings.get(1).team();

            String third =
                    standings.get(2).team();

            String fourth =
                    standings.get(3).team();

            firstPlaceCounts.merge(
                    first,
                    1,
                    Integer::sum
            );

            secondPlaceCounts.merge(
                    second,
                    1,
                    Integer::sum
            );

            thirdPlaceCounts.merge(
                    third,
                    1,
                    Integer::sum
            );

            fourthPlaceCounts.merge(
                    fourth,
                    1,
                    Integer::sum
            );
            
            // --------------------------------------------------
            // Semi-final 1
            // 1st vs 4th
            // --------------------------------------------------

            String semiFinal1Winner =
                    simulateWinner(
                            first,
                            fourth,
                            probabilityCache
                    );

            // --------------------------------------------------
            // Semi-final 2
            // 2nd vs 3rd
            // --------------------------------------------------

            String semiFinal2Winner =
                    simulateWinner(
                            second,
                            third,
                            probabilityCache
                    );

            finalAppearances.merge(
                    semiFinal1Winner,
                    1,
                    Integer::sum
            );

            finalAppearances.merge(
                    semiFinal2Winner,
                    1,
                    Integer::sum
            );
            
            // --------------------------------------------------
            // Final
            // --------------------------------------------------

            String champion =
                    simulateWinner(
                            semiFinal1Winner,
                            semiFinal2Winner,
                            probabilityCache
                    );

            championshipWins.merge(
                    champion,
                    1,
                    Integer::sum
            );
        }

        // --------------------------------------------------
        // 5. Build result
        // --------------------------------------------------

        List<ODIMonteCarloTeamResult> results =
                new ArrayList<>();

        for (String team : request.teams()) {

            int tournamentWins =
                    championshipWins.getOrDefault(
                            team,
                            0
                    );

            int qualificationCount =
                    qualificationCounts.getOrDefault(
                            team,
                            0
                    );
            
            int finalAppearanceCount =
                    finalAppearances.getOrDefault(
                            team,
                            0
                    );

            int firstPlaceCount =
                    firstPlaceCounts.getOrDefault(
                            team,
                            0
                    );

            int secondPlaceCount =
                    secondPlaceCounts.getOrDefault(
                            team,
                            0
                    );

            int thirdPlaceCount =
                    thirdPlaceCounts.getOrDefault(
                            team,
                            0
                    );

            int fourthPlaceCount =
                    fourthPlaceCounts.getOrDefault(
                            team,
                            0
                    );

            double championshipProbability =
                    ((double) tournamentWins
                            / simulations)
                            * 100.0;

            double qualificationProbability =
                    ((double) qualificationCount
                            / simulations)
                            * 100.0;
            
            double finalAppearanceProbability =
                    ((double) finalAppearanceCount
                            / simulations)
                            * 100.0;

            double firstPlaceProbability =
                    ((double) firstPlaceCount
                            / simulations)
                            * 100.0;

            double secondPlaceProbability =
                    ((double) secondPlaceCount
                            / simulations)
                            * 100.0;

            double thirdPlaceProbability =
                    ((double) thirdPlaceCount
                            / simulations)
                            * 100.0;

            double fourthPlaceProbability =
                    ((double) fourthPlaceCount
                            / simulations)
                            * 100.0;
            
            finalAppearanceProbability =
                    roundTwoDecimals(
                            finalAppearanceProbability
                    );

            firstPlaceProbability =
                    roundTwoDecimals(
                            firstPlaceProbability
                    );

            secondPlaceProbability =
                    roundTwoDecimals(
                            secondPlaceProbability
                    );

            thirdPlaceProbability =
                    roundTwoDecimals(
                            thirdPlaceProbability
                    );

            fourthPlaceProbability =
                    roundTwoDecimals(
                            fourthPlaceProbability
                    );

            championshipProbability =
                    roundTwoDecimals(
                            championshipProbability
                    );

            qualificationProbability =
                    roundTwoDecimals(
                            qualificationProbability
                    );

            results.add(
                    new ODIMonteCarloTeamResult(
                            team,
                            tournamentWins,
                            championshipProbability,
                            qualificationCount,
                            qualificationProbability,
                            finalAppearanceCount,
                            finalAppearanceProbability,
                            firstPlaceCount,
                            firstPlaceProbability,
                            secondPlaceCount,
                            secondPlaceProbability,
                            thirdPlaceCount,
                            thirdPlaceProbability,
                            fourthPlaceCount,
                            fourthPlaceProbability
                    )
            );
        }

        // --------------------------------------------------
        // 6. Sort by championship probability
        // --------------------------------------------------

        results.sort(
                (a, b) -> {

                    int championshipCompare =
                            Double.compare(
                                    b.championshipProbability(),
                                    a.championshipProbability()
                            );

                    if (championshipCompare != 0) {
                        return championshipCompare;
                    }

                    return Double.compare(
                            b.qualificationProbability(),
                            a.qualificationProbability()
                    );
                }
        );

        return new ODIMonteCarloResult(
                simulations,
                results
        );
    }

    // ======================================================
    // Probability cache
    // ======================================================

    private Map<String, ODIMatchProbability> buildProbabilityCache(
            List<ODIFixtureResponse> fixtures,
            String predictionDate
    ) {

        Map<String, ODIMatchProbability> cache =
                new HashMap<>();

        for (ODIFixtureResponse fixture :
                fixtures) {

            String teamA =
                    fixture.teamA();

            String teamB =
                    fixture.teamB();

            String key =
                    buildKey(
                            teamA,
                            teamB
                    );

            if (cache.containsKey(key)) {
                continue;
            }

            ODIPredictionRequest predictionRequest =
                    new ODIPredictionRequest(
                            teamA,
                            teamB,
                            fixture.venue(),
                            predictionDate
                    );

            ODIPredictionResponse prediction =
                    mlPredictionService.predictODI(
                            predictionRequest
                    );

            ODIMatchProbability probability =
                    new ODIMatchProbability(
                            teamA,
                            teamB,
                            prediction.teamAWinProbability(),
                            prediction.teamBWinProbability()
                    );

            cache.put(
                    key,
                    probability
            );
        }

        return cache;
    }

    // ======================================================
    // League simulation
    // ======================================================

    private List<ODITeamStanding> simulateLeague(
            List<String> teams,
            List<ODIFixtureResponse> fixtures,
            Map<String, ODIMatchProbability> probabilityCache
    ) {

        Map<String, StandingState> states =
                new LinkedHashMap<>();

        for (String team : teams) {

            states.put(
                    team,
                    new StandingState(team)
            );
        }

        for (ODIFixtureResponse fixture :
                fixtures) {

            String winner =
                    simulateWinner(
                            fixture.teamA(),
                            fixture.teamB(),
                            probabilityCache
                    );

            StandingState teamA =
                    states.get(
                            fixture.teamA()
                    );

            StandingState teamB =
                    states.get(
                            fixture.teamB()
                    );

            teamA.matches++;
            teamB.matches++;

            if (winner.equals(teamA.team)) {

                teamA.wins++;
                teamA.points += 2;

                teamB.losses++;

            } else {

                teamB.wins++;
                teamB.points += 2;

                teamA.losses++;
            }
        }

        List<ODITeamStanding> standings =
                new ArrayList<>();

        for (StandingState state :
                states.values()) {

            double winPercentage =
                    state.matches == 0
                            ? 0.0
                            : ((double) state.wins
                            / state.matches)
                            * 100.0;

            winPercentage =
                    roundTwoDecimals(
                            winPercentage
                    );

            standings.add(
                    new ODITeamStanding(
                            state.team,
                            state.matches,
                            state.wins,
                            state.losses,
                            0,
                            0,
                            state.points,
                            winPercentage
                    )
            );
        }

        // --------------------------------------------------
        // Sort standings
        // --------------------------------------------------

        standings.sort(
                (a, b) -> {

                    int pointsCompare =
                            Integer.compare(
                                    b.points(),
                                    a.points()
                            );

                    if (pointsCompare != 0) {
                        return pointsCompare;
                    }

                    int winPercentageCompare =
                            Double.compare(
                                    b.winPercentage(),
                                    a.winPercentage()
                            );

                    if (winPercentageCompare != 0) {
                        return winPercentageCompare;
                    }

                    return a.team().compareTo(
                            b.team()
                    );
                }
        );

        return standings;
    }

    // ======================================================
    // Match winner
    // ======================================================

    private String simulateWinner(
            String teamA,
            String teamB,
            Map<String, ODIMatchProbability> probabilityCache
    ) {

        String key =
                buildKey(
                        teamA,
                        teamB
                );

        ODIMatchProbability probability =
                probabilityCache.get(key);

        if (probability == null) {

            throw new IllegalStateException(
                    "Probability not found for "
                            + teamA
                            + " vs "
                            + teamB
            );
        }

        double teamAProbability;

        if (probability.teamA().equals(teamA)) {

            teamAProbability =
                    probability.teamAWinProbability();

        } else {

            teamAProbability =
                    probability.teamBWinProbability();
        }

        double random =
                ThreadLocalRandom.current()
                        .nextDouble();

        return random < teamAProbability
                ? teamA
                : teamB;
    }

    // ======================================================
    // Order-independent matchup key
    // ======================================================

    private String buildKey(
            String teamA,
            String teamB
    ) {

        if (teamA.compareTo(teamB) < 0) {

            return teamA
                    + "||"
                    + teamB;
        }

        return teamB
                + "||"
                + teamA;
    }

    // ======================================================
    // Round to two decimal places
    // ======================================================

    private double roundTwoDecimals(
            double value
    ) {

        return Math.round(
                value * 100.0
        ) / 100.0;
    }

    // ======================================================
    // Internal standings state
    // ======================================================

    private static class StandingState {

        private final String team;

        private int matches;
        private int wins;
        private int losses;
        private int points;

        private StandingState(
                String team
        ) {

            this.team = team;
        }
    }
}