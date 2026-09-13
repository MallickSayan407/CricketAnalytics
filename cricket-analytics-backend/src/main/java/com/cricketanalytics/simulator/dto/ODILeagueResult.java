package com.cricketanalytics.simulator.dto;

import java.util.List;

public record ODILeagueResult(
        int totalMatches,
        List<ODITeamStanding> standings
) {
}