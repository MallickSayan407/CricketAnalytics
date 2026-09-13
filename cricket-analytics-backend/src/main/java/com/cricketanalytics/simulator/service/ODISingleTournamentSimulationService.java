package com.cricketanalytics.simulator.service;

import com.cricketanalytics.ml.dto.ODIPredictionRequest;
import com.cricketanalytics.ml.dto.ODIPredictionResponse;
import com.cricketanalytics.ml.service.MLPredictionService;
import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODIFixtureResponse;
import com.cricketanalytics.simulator.dto.ODISimulatedMatch;
import com.cricketanalytics.simulator.dto.ODISimulatedTournamentResult;
import com.cricketanalytics.simulator.dto.ODITeamStanding;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

@Service
public class ODISingleTournamentSimulationService {

    private final ODISimulatorService fixtureService;
    private final MLPredictionService mlPredictionService;

    public ODISingleTournamentSimulationService(
            ODISimulatorService fixtureService,
            MLPredictionService mlPredictionService
    ) {
        this.fixtureService = fixtureService;
        this.mlPredictionService = mlPredictionService;
    }

    public ODISimulatedTournamentResult simulate(
            ODIFixtureRequest request
    ) {

        // --------------------------------------------------
        // 1. Generate 28 league fixtures
        // --------------------------------------------------

        List<ODIFixtureResponse> fixtures =
                fixtureService.generateFixtures(request);

        // --------------------------------------------------
        // 2. Build probability cache
        // --------------------------------------------------

        Map<String, MatchProbability> probabilityCache =
                buildProbabilityCache(
                        fixtures,
                        request.predictionDate()
                );

        // --------------------------------------------------
        // 3. Initialize standings
        // --------------------------------------------------

        Map<String, StandingState> states =
                new LinkedHashMap<>();

        for (String team : request.teams()) {

            states.put(
                    team,
                    new StandingState(team)
            );
        }

        // --------------------------------------------------
        // 4. Simulate league
        // --------------------------------------------------

        for (ODIFixtureResponse fixture : fixtures) {

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

        // --------------------------------------------------
        // 5. Convert to sorted standings
        // --------------------------------------------------

        List<ODITeamStanding> standings =
                buildStandings(states);

        // --------------------------------------------------
        // 6. Top four qualify
        // --------------------------------------------------

        String first =
                standings.get(0).team();

        String second =
                standings.get(1).team();

        String third =
                standings.get(2).team();

        String fourth =
                standings.get(3).team();

        // --------------------------------------------------
        // 7. Semi-final 1
        // 1st vs 4th
        // --------------------------------------------------

        ODISimulatedMatch semiFinal1 =
                simulateKnockoutMatch(
                        "SEMI_FINAL_1",
                        first,
                        fourth,
                        probabilityCache
                );

        // --------------------------------------------------
        // 8. Semi-final 2
        // 2nd vs 3rd
        // --------------------------------------------------

        ODISimulatedMatch semiFinal2 =
                simulateKnockoutMatch(
                        "SEMI_FINAL_2",
                        second,
                        third,
                        probabilityCache
                );

        // --------------------------------------------------
        // 9. Final
        // --------------------------------------------------

        ODISimulatedMatch finalMatch =
                simulateKnockoutMatch(
                        "FINAL",
                        semiFinal1.winner(),
                        semiFinal2.winner(),
                        probabilityCache
                );

        // --------------------------------------------------
        // 10. Champion
        // --------------------------------------------------

        String champion =
                finalMatch.winner();

        return new ODISimulatedTournamentResult(
                fixtures.size(),
                standings,
                semiFinal1,
                semiFinal2,
                finalMatch,
                champion
        );
    }

    // ======================================================
    // Build probability cache
    // ======================================================

    private Map<String, MatchProbability> buildProbabilityCache(
            List<ODIFixtureResponse> fixtures,
            String predictionDate
    ) {

        Map<String, MatchProbability> cache =
                new HashMap<>();

        for (ODIFixtureResponse fixture :
                fixtures) {

            String key =
                    buildKey(
                            fixture.teamA(),
                            fixture.teamB()
                    );

            if (cache.containsKey(key)) {
                continue;
            }

            ODIPredictionRequest predictionRequest =
                    new ODIPredictionRequest(
                            fixture.teamA(),
                            fixture.teamB(),
                            fixture.venue(),
                            predictionDate
                    );

            ODIPredictionResponse prediction =
                    mlPredictionService.predictODI(
                            predictionRequest
                    );

            MatchProbability probability =
                    new MatchProbability(
                            fixture.teamA(),
                            fixture.teamB(),
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
    // Simulate knockout match
    // ======================================================

    private ODISimulatedMatch simulateKnockoutMatch(
            String stage,
            String teamA,
            String teamB,
            Map<String, MatchProbability> probabilityCache
    ) {

        MatchProbability probability =
                probabilityCache.get(
                        buildKey(
                                teamA,
                                teamB
                        )
                );

        /*
         * Normally every possible semifinal/final matchup
         * is already present in the 8-team league fixture cache.
         *
         * If a matchup was not part of the league fixtures,
         * calculate its probability here.
         */
        if (probability == null) {

            throw new IllegalStateException(
                    "Probability not found for knockout matchup: "
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

        double teamBProbability =
                1.0 - teamAProbability;

        double randomValue =
                ThreadLocalRandom.current()
                        .nextDouble();

        String winner =
                randomValue < teamAProbability
                        ? teamA
                        : teamB;

        return new ODISimulatedMatch(
                stage,
                teamA,
                teamB,
                winner,
                roundTwoDecimals(
                        teamAProbability
                ),
                roundTwoDecimals(
                        teamBProbability
                )
        );
    }

    // ======================================================
    // Simulate winner
    // ======================================================

    private String simulateWinner(
            String teamA,
            String teamB,
            Map<String, MatchProbability> probabilityCache
    ) {

        MatchProbability probability =
                probabilityCache.get(
                        buildKey(
                                teamA,
                                teamB
                        )
                );

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

        double randomValue =
                ThreadLocalRandom.current()
                        .nextDouble();

        return randomValue < teamAProbability
                ? teamA
                : teamB;
    }

    // ======================================================
    // Build standings
    // ======================================================

    private List<ODITeamStanding> buildStandings(
            Map<String, StandingState> states
    ) {

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

            standings.add(
                    new ODITeamStanding(
                            state.team,
                            state.matches,
                            state.wins,
                            state.losses,
                            0,
                            0,
                            state.points,
                            roundTwoDecimals(
                                    winPercentage
                            )
                    )
            );
        }

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
    // Round
    // ======================================================

    private double roundTwoDecimals(
            double value
    ) {

        return Math.round(
                value * 100.0
        ) / 100.0;
    }

    // ======================================================
    // Internal probability object
    // ======================================================

    private record MatchProbability(
            String teamA,
            String teamB,
            double teamAWinProbability,
            double teamBWinProbability
    ) {
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