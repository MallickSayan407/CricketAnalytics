package com.cricketanalytics.simulator.dto;

public record ODITeamStanding(
        String team,
        int matches,
        int wins,
        int losses,
        int ties,
        int noResults,
        int points,
        double winPercentage
) {
}