package com.cricketanalytics.ml.controller;

import com.cricketanalytics.ml.dto.ODIPredictionRequest;
import com.cricketanalytics.ml.dto.ODIPredictionResponse;
import com.cricketanalytics.ml.service.MLPredictionService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ml")
@CrossOrigin(origins = "*")
public class MLPredictionController {

    private final MLPredictionService mlPredictionService;

    public MLPredictionController(
            MLPredictionService mlPredictionService) {

        this.mlPredictionService = mlPredictionService;
    }

    @PostMapping("/predict/odi")
    public ResponseEntity<ODIPredictionResponse> predictODI(
            @RequestBody ODIPredictionRequest request) {

        ODIPredictionResponse response =
                mlPredictionService.predictODI(request);

        return ResponseEntity.ok(response);
    }
}