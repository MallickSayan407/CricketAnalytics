package com.cricketanalytics.simulator.controller;

import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODIFixtureResponse;
import com.cricketanalytics.simulator.service.ODISimulatorService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/simulator/odi")
@CrossOrigin(origins = "*")
public class ODISimulatorController {

    private final ODISimulatorService simulatorService;


    public ODISimulatorController(
            ODISimulatorService simulatorService) {

        this.simulatorService = simulatorService;
    }


    @PostMapping("/fixtures")
    public ResponseEntity<List<ODIFixtureResponse>>
    generateFixtures(
            @RequestBody ODIFixtureRequest request) {

        List<ODIFixtureResponse> fixtures =
                simulatorService.generateFixtures(request);

        return ResponseEntity.ok(fixtures);
    }
}