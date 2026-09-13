package com.cricketanalytics.simulator.dto;

public record ODISimulatedMatch(
        String stage,
        String teamA,
        String teamB,
        String winner,
        double teamAWinProbability,
        double teamBWinProbability
) {
}