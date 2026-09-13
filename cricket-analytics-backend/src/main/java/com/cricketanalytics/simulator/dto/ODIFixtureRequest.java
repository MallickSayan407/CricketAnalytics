package com.cricketanalytics.simulator.dto;

import java.util.List;

public record ODIFixtureRequest(
        List<String> teams,
        String venue,
        String predictionDate
) {
}