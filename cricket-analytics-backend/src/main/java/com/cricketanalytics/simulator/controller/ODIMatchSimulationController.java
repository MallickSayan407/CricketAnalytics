package com.cricketanalytics.simulator.controller;

import com.cricketanalytics.simulator.dto.ODIMatchSimulationRequest;
import com.cricketanalytics.simulator.dto.ODIMatchSimulationResponse;
import com.cricketanalytics.simulator.service.ODIMatchSimulationService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/simulator/odi")
@CrossOrigin(origins = "*")
public class ODIMatchSimulationController {

    private final ODIMatchSimulationService simulationService;


    public ODIMatchSimulationController(
            ODIMatchSimulationService simulationService) {

        this.simulationService =
                simulationService;
    }


    @PostMapping("/match")
    public ResponseEntity<ODIMatchSimulationResponse>
    simulateMatch(
            @RequestBody ODIMatchSimulationRequest request) {

        ODIMatchSimulationResponse response =
                simulationService.simulateMatch(
                        request
                );

        return ResponseEntity.ok(response);
    }
}