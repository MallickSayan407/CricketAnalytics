package com.cricketanalytics.simulator.controller;

import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODISimulatedTournamentResult;
import com.cricketanalytics.simulator.service.ODISingleTournamentSimulationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/simulator/odi")
@CrossOrigin(origins = "*")
public class ODISingleTournamentSimulationController {

    private final ODISingleTournamentSimulationService simulationService;

    public ODISingleTournamentSimulationController(
            ODISingleTournamentSimulationService simulationService
    ) {
        this.simulationService = simulationService;
    }

    @PostMapping("/tournament")
    public ResponseEntity<ODISimulatedTournamentResult> simulate(
            @RequestBody ODIFixtureRequest request
    ) {

        ODISimulatedTournamentResult result =
                simulationService.simulate(
                        request
                );

        return ResponseEntity.ok(result);
    }
}