package com.cricketanalytics.simulator.controller;

import com.cricketanalytics.simulator.dto.ODIFixtureRequest;
import com.cricketanalytics.simulator.dto.ODILeagueResult;
import com.cricketanalytics.simulator.service.ODILeagueSimulationService;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/simulator/odi")
@CrossOrigin(origins = "*")
public class ODILeagueSimulationController {

    private final ODILeagueSimulationService leagueService;


    public ODILeagueSimulationController(
            ODILeagueSimulationService leagueService) {

        this.leagueService = leagueService;
    }


    @PostMapping("/league")
    public ResponseEntity<ODILeagueResult>
    simulateLeague(
            @RequestBody ODIFixtureRequest request) {

        ODILeagueResult result =
                leagueService.simulateLeague(request);

        return ResponseEntity.ok(result);
    }
}