package com.cricketanalytics.simulator.controller;

import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODIMonteCarloResult;
import com.cricketanalytics.simulator.service.ODIMonteCarloSimulationService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/simulator/odi")
@CrossOrigin(origins = "*")
public class ODIMonteCarloSimulationController {

    private final ODIMonteCarloSimulationService monteCarloService;

    public ODIMonteCarloSimulationController(
            ODIMonteCarloSimulationService monteCarloService
    ) {
        this.monteCarloService = monteCarloService;
    }

    @PostMapping("/monte-carlo")
    public ResponseEntity<ODIMonteCarloResult> simulate(
            @RequestBody ODIFixtureRequest request,
            @RequestParam(defaultValue = "100") int simulations
    ) {

        ODIMonteCarloResult result =
                monteCarloService.simulate(
                        request,
                        simulations
                );

        return ResponseEntity.ok(result);
    }
}