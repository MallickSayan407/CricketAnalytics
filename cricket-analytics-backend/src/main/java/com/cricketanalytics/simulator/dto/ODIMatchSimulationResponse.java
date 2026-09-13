package com.cricketanalytics.simulator.dto;

public record ODIMatchSimulationResponse(
        String teamA,
        String teamB,
        String venue,
        String predictedWinner,
        String simulatedWinner,
        double teamAWinProbability,
        double teamBWinProbability,
        double randomValue
) {
}