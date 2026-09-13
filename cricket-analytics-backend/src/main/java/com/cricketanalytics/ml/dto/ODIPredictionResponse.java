package com.cricketanalytics.ml.dto;

public record ODIPredictionResponse(

        String teamA,

        String teamB,

        String venue,

        String predictionDate,

        double teamAWinProbability,

        double teamBWinProbability,

        String predictedWinner,

        String modelVersion,

        String modelType,

        String featureSet,

        int featureCount,

        int teamAMatchesBefore,

        int teamBMatchesBefore,

        int headToHeadMatchesBefore,

        int teamAVenueMatchesBefore,

        int teamBVenueMatchesBefore

) {
}