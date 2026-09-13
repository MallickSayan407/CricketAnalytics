package com.cricketanalytics.simulator.dto;

public record ODIMatchSimulationRequest(
        String teamA,
        String teamB,
        String venue,
        String predictionDate
) {
}