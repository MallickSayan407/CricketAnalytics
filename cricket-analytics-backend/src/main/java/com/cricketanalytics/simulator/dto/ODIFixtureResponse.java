package com.cricketanalytics.simulator.dto;

public record ODIFixtureResponse(
        int matchNumber,
        String teamA,
        String teamB,
        String venue
) {
}