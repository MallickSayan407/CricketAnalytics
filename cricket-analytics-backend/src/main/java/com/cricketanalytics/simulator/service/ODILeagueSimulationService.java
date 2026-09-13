package com.cricketanalytics.simulator.service;

import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODIFixtureResponse;
import com.cricketanalytics.simulator.dto.ODIMatchSimulationRequest;
import com.cricketanalytics.simulator.dto.ODIMatchSimulationResponse;
import com.cricketanalytics.simulator.dto.ODITeamStanding;
import com.cricketanalytics.simulator.dto.ODILeagueResult;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class ODILeagueSimulationService {

    private final ODISimulatorService fixtureService;
    private final ODIMatchSimulationService matchSimulationService;


    public ODILeagueSimulationService(
            ODISimulatorService fixtureService,
            ODIMatchSimulationService matchSimulationService) {

        this.fixtureService = fixtureService;
        this.matchSimulationService =
                matchSimulationService;
    }


    public ODILeagueResult simulateLeague(
            ODIFixtureRequest request) {


        // =====================================================
        // GENERATE FIXTURES
        // =====================================================

        List<ODIFixtureResponse> fixtures =
                fixtureService.generateFixtures(request);


        // =====================================================
        // CREATE STANDING STATE
        // =====================================================

        Map<String, TeamStandingState> table =
                new LinkedHashMap<>();


        for (String team : request.teams()) {

            table.put(
                    team,
                    new TeamStandingState(team)
            );
        }


        // =====================================================
        // SIMULATE EVERY MATCH
        // =====================================================

        for (ODIFixtureResponse fixture : fixtures) {

        	ODIMatchSimulationRequest matchRequest =
        	        new ODIMatchSimulationRequest(
        	                fixture.teamA(),
        	                fixture.teamB(),
        	                fixture.venue(),
        	                request.predictionDate()
        	        );


            ODIMatchSimulationResponse result =
                    matchSimulationService
                            .simulateMatch(matchRequest);


            String winner =
                    result.simulatedWinner();


            TeamStandingState teamA =
                    table.get(fixture.teamA());

            TeamStandingState teamB =
                    table.get(fixture.teamB());


            teamA.matches++;
            teamB.matches++;


            // =================================================
            // UPDATE WINNER / LOSER
            // =================================================

            if (winner.equals(fixture.teamA())) {

                teamA.wins++;
                teamA.points += 2;

                teamB.losses++;

            } else {

                teamB.wins++;
                teamB.points += 2;

                teamA.losses++;
            }
        }


        // =====================================================
        // CONVERT TO RESPONSE
        // =====================================================

        List<ODITeamStanding> standings =
                new ArrayList<>();


        for (TeamStandingState state :
                table.values()) {

            double winPercentage =
                    state.matches == 0
                            ? 0.0
                            : (state.wins * 100.0)
                                    / state.matches;


            standings.add(
                    new ODITeamStanding(
                            state.team,
                            state.matches,
                            state.wins,
                            state.losses,
                            state.ties,
                            state.noResults,
                            state.points,
                            Math.round(
                                    winPercentage * 100.0
                            ) / 100.0
                    )
            );
        }


        // =====================================================
        // SORT TABLE
        // =====================================================

        standings.sort(
                Comparator
                        .comparingInt(
                                ODITeamStanding::points
                        )
                        .reversed()
                        .thenComparing(
                                ODITeamStanding::winPercentage,
                                Comparator.reverseOrder()
                        )
                        .thenComparing(
                                ODITeamStanding::team
                        )
        );


        return new ODILeagueResult(
                fixtures.size(),
                standings
        );
    }


    // =========================================================
    // INTERNAL STANDING STATE
    // =========================================================

    private static class TeamStandingState {

        private final String team;

        private int matches;
        private int wins;
        private int losses;
        private int ties;
        private int noResults;
        private int points;


        private TeamStandingState(String team) {

            this.team = team;
        }
    }
}