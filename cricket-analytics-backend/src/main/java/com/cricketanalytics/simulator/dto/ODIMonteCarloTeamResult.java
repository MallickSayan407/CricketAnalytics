package com.cricketanalytics.simulator.dto;

public record ODIMonteCarloTeamResult(
        String team,
        int tournamentWins,
        double championshipProbability,
        int qualificationCount,
        double qualificationProbability,
        int finalAppearances,
        double finalAppearanceProbability,
        int firstPlaceCount,
        double firstPlaceProbability,
        int secondPlaceCount,
        double secondPlaceProbability,
        int thirdPlaceCount,
        double thirdPlaceProbability,
        int fourthPlaceCount,
        double fourthPlaceProbability
) {
}