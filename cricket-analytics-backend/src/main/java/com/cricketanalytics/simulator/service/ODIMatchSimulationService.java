package com.cricketanalytics.simulator.service;

import com.cricketanalytics.ml.dto.ODIPredictionRequest;
import com.cricketanalytics.ml.dto.ODIPredictionResponse;
import com.cricketanalytics.ml.service.MLPredictionService;
import com.cricketanalytics.simulator.dto.ODIMatchSimulationRequest;
import com.cricketanalytics.simulator.dto.ODIMatchSimulationResponse;

import org.springframework.stereotype.Service;

import java.util.concurrent.ThreadLocalRandom;

@Service
public class ODIMatchSimulationService {

    private final MLPredictionService mlPredictionService;


    public ODIMatchSimulationService(
            MLPredictionService mlPredictionService) {

        this.mlPredictionService =
                mlPredictionService;
    }


    public ODIMatchSimulationResponse simulateMatch(
            ODIMatchSimulationRequest request) {


        // =====================================================
        // VALIDATION
        // =====================================================

        if (request == null) {

            throw new IllegalArgumentException(
                    "Match simulation request cannot be null."
            );
        }


        if (request.teamA() == null
                || request.teamA().isBlank()) {

            throw new IllegalArgumentException(
                    "Team A is required."
            );
        }


        if (request.teamB() == null
                || request.teamB().isBlank()) {

            throw new IllegalArgumentException(
                    "Team B is required."
            );
        }


        if (request.teamA()
                .trim()
                .equalsIgnoreCase(
                        request.teamB().trim()
                )) {

            throw new IllegalArgumentException(
                    "Team A and Team B must be different."
            );
        }


        if (request.venue() == null
                || request.venue().isBlank()) {

            throw new IllegalArgumentException(
                    "Venue is required."
            );
        }


        if (request.predictionDate() == null
                || request.predictionDate().isBlank()) {

            throw new IllegalArgumentException(
                    "Prediction date is required."
            );
        }


        // =====================================================
        // ASK ML MODEL FOR PROBABILITIES
        // =====================================================

        ODIPredictionRequest predictionRequest =
                new ODIPredictionRequest(
                        request.teamA(),
                        request.teamB(),
                        request.venue(),
                        request.predictionDate()
                );


        ODIPredictionResponse prediction =
                mlPredictionService.predictODI(
                        predictionRequest
                );


        // =====================================================
        // EXTRACT PROBABILITY
        // =====================================================

        double teamAProbability =
                prediction.teamAWinProbability();


        double teamBProbability =
                prediction.teamBWinProbability();


        // =====================================================
        // GENERATE RANDOM NUMBER
        // =====================================================

        double randomValue =
                ThreadLocalRandom
                        .current()
                        .nextDouble();


        // =====================================================
        // SIMULATE WINNER
        // =====================================================

        String simulatedWinner;


        if (randomValue < teamAProbability) {

            simulatedWinner =
                    request.teamA();

        } else {

            simulatedWinner =
                    request.teamB();
        }


        // =====================================================
        // RETURN RESULT
        // =====================================================

        return new ODIMatchSimulationResponse(
                request.teamA(),
                request.teamB(),
                request.venue(),
                prediction.predictedWinner(),
                simulatedWinner,
                teamAProbability,
                teamBProbability,
                randomValue
        );
    }
}