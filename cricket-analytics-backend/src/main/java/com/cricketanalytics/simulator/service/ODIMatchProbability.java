package com.cricketanalytics.simulator.service;

public record ODIMatchProbability(
        String teamA,
        String teamB,
        double teamAWinProbability,
        double teamBWinProbability
) {
}