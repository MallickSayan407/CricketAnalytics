package com.cricketanalytics.ml.service;

import com.cricketanalytics.ml.dto.ODIPredictionRequest;
import com.cricketanalytics.ml.dto.ODIPredictionResponse;
import java.nio.charset.StandardCharsets;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import tools.jackson.core.JacksonException;
import tools.jackson.databind.ObjectMapper;

@Service
public class MLPredictionService {

    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;
    private final String mlApiBaseUrl;

    public MLPredictionService(
            ObjectMapper objectMapper,
            @Value("${ml.api.base-url}") String mlApiBaseUrl) {

        this.objectMapper = objectMapper;
        this.mlApiBaseUrl = mlApiBaseUrl;

        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public ODIPredictionResponse predictODI(
            ODIPredictionRequest request) {

        System.out.println();
        System.out.println("==========================================");
        System.out.println("CALLING ML API");
        System.out.println("==========================================");
        System.out.println("Team A : " + request.teamA());
        System.out.println("Team B : " + request.teamB());
        System.out.println("Venue  : " + request.venue());
        System.out.println("Date   : " + request.predictionDate());

        try {

            // Convert the Java request into JSON.
            String jsonBody =
                    objectMapper.writeValueAsString(request);

            System.out.println();
            System.out.println("JSON SENT TO ML API:");
            System.out.println(jsonBody);

            // Build the HTTP request explicitly.
            byte[] jsonBytes =
                    jsonBody.getBytes(StandardCharsets.UTF_8);

            HttpRequest httpRequest =
                    HttpRequest.newBuilder()
                            .uri(URI.create(
                                    mlApiBaseUrl + "/predict/odi"
                            ))
                            .timeout(Duration.ofSeconds(60))
                            .header(
                                    "Content-Type",
                                    "application/json"
                            )
                            .header(
                                    "Accept",
                                    "application/json"
                            )
                            .POST(
                                    HttpRequest.BodyPublishers
                                            .ofByteArray(jsonBytes)
                            )
                            .build();

            System.out.println();
            System.out.println(
                    "ML API URL : "
                            + mlApiBaseUrl
                            + "/predict/odi"
            );

            System.out.println(
                    "Sending HTTP request..."
            );

            HttpResponse<String> httpResponse =
                    httpClient.send(
                            httpRequest,
                            HttpResponse.BodyHandlers.ofString()
                    );

            System.out.println();
            System.out.println(
                    "ML API HTTP STATUS : "
                            + httpResponse.statusCode()
            );

            System.out.println(
                    "ML API RAW RESPONSE:"
            );

            System.out.println(
                    httpResponse.body()
            );

            System.out.println();

            if (httpResponse.statusCode() < 200
                    || httpResponse.statusCode() >= 300) {

                throw new RuntimeException(
                        "ML API returned HTTP "
                                + httpResponse.statusCode()
                                + ": "
                                + httpResponse.body()
                );
            }

            ODIPredictionResponse response =
                    objectMapper.readValue(
                            httpResponse.body(),
                            ODIPredictionResponse.class
                    );

            System.out.println(
                    "ML API RESPONSE PARSED SUCCESSFULLY"
            );

            System.out.println(
                    "Predicted winner : "
                            + response.predictedWinner()
            );

            System.out.println(
                    "Team A probability : "
                            + response.teamAWinProbability()
            );

            System.out.println(
                    "Team B probability : "
                            + response.teamBWinProbability()
            );

            System.out.println(
                    "=========================================="
            );

            return response;

        } catch (JacksonException ex) {

            System.err.println();
            System.err.println(
                    "JSON PROCESSING ERROR"
            );

            System.err.println(
                    "Message : "
                            + ex.getMessage()
            );

            System.err.println(
                    "=========================================="
            );

            throw new RuntimeException(
                    "Could not process ML API JSON.",
                    ex
            );

        } catch (InterruptedException ex) {

            Thread.currentThread().interrupt();

            System.err.println();
            System.err.println(
                    "ML API REQUEST INTERRUPTED"
            );

            throw new RuntimeException(
                    "ML API request was interrupted.",
                    ex
            );

        } catch (Exception ex) {

            System.err.println();
            System.err.println(
                    "ML API CONNECTION/PROCESSING ERROR"
            );

            System.err.println(
                    "Type    : "
                            + ex.getClass().getName()
            );

            System.err.println(
                    "Message : "
                            + ex.getMessage()
            );

            System.err.println(
                    "=========================================="
            );

            ex.printStackTrace();

            throw new RuntimeException(
                    "Could not communicate with ML API: "
                            + ex.getMessage(),
                    ex
            );
        }
    }
}