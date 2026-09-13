package com.cricketanalytics.simulator.dto;

import java.util.List;

public record ODISimulatedTournamentResult(
        int leagueMatches,
        List<ODITeamStanding> standings,
        ODISimulatedMatch semiFinal1,
        ODISimulatedMatch semiFinal2,
        ODISimulatedMatch finalMatch,
        String champion
) {
}