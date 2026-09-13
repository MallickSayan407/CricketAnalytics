package com.cricketanalytics.ml.dto;

public record ODIPredictionRequest(
        String teamA,
        String teamB,
        String venue,
        String predictionDate
) {
}