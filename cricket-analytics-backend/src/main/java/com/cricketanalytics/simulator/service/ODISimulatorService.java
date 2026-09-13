package com.cricketanalytics.simulator.service;

import com.cricketanalytics.entity.Team;
import com.cricketanalytics.repository.TeamRepository;
import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODIFixtureResponse;

import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

@Service
public class ODISimulatorService {

    private final TeamRepository teamRepository;

    public ODISimulatorService(
            TeamRepository teamRepository) {

        this.teamRepository = teamRepository;
    }


    public List<ODIFixtureResponse> generateFixtures(
            ODIFixtureRequest request) {

        // =====================================================
        // VALIDATE REQUEST
        // =====================================================

        if (request == null) {

            throw new IllegalArgumentException(
                    "Tournament request cannot be null."
            );
        }


        if (request.teams() == null) {

            throw new IllegalArgumentException(
                    "Team list cannot be null."
            );
        }


        if (request.teams().size() != 8) {

            throw new IllegalArgumentException(
                    "The first ODI simulator version requires exactly 8 teams."
            );
        }


        if (request.venue() == null
                || request.venue().isBlank()) {

            throw new IllegalArgumentException(
                    "Venue is required."
            );
        }


        // =====================================================
        // CLEAN TEAM NAMES
        // =====================================================

        List<String> teams = request.teams()
                .stream()
                .map(String::trim)
                .toList();


        // =====================================================
        // CHECK DUPLICATE TEAMS
        // =====================================================

        Set<String> uniqueTeams =
                new HashSet<>(teams);


        if (uniqueTeams.size() != teams.size()) {

            throw new IllegalArgumentException(
                    "Tournament teams must be unique."
            );
        }


        // =====================================================
        // VERIFY TEAMS EXIST IN DATABASE
        // =====================================================

        for (String teamName : teams) {

            if (teamName.isBlank()) {

                throw new IllegalArgumentException(
                        "Team name cannot be blank."
                );
            }


            Team team =
                    teamRepository
                            .findByNameAndGender(
                                    teamName,
                                    "male"
                            )
                            .orElseThrow(() ->
                                    new IllegalArgumentException(
                                            "ODI team not found in database: "
                                                    + teamName
                                    )
                            );


            /*
             * The variable is intentionally retrieved here.
             * The existence check above is what we need.
             */

            if (team.getId() == null) {

                throw new IllegalArgumentException(
                        "Invalid team record: "
                                + teamName
                );
            }
        }


        // =====================================================
        // GENERATE ROUND-ROBIN FIXTURES
        // =====================================================

        List<ODIFixtureResponse> fixtures =
                new ArrayList<>();


        int matchNumber = 1;


        /*
         * Every team plays every other team exactly once.
         *
         * Example:
         *
         * India vs Australia
         * India vs England
         * India vs South Africa
         * ...
         */

        for (int i = 0; i < teams.size(); i++) {

            for (int j = i + 1;
                 j < teams.size();
                 j++) {

                fixtures.add(
                        new ODIFixtureResponse(
                                matchNumber++,
                                teams.get(i),
                                teams.get(j),
                                request.venue()
                        )
                );
            }
        }


        return fixtures;
    }
}