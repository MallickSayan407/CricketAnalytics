package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.PlayerTrendResponseDTO;
import com.cricketanalytics.analytics.service.PlayerTrendService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics/players")
@RequiredArgsConstructor
public class PlayerTrendController {

    private final PlayerTrendService playerTrendService;

    @GetMapping("/{playerId}/trends")
    public ResponseEntity<PlayerTrendResponseDTO> getPlayerTrends(

            @PathVariable("playerId")
            Long playerId,

            @RequestParam(required = false)
            Long competitionId,

            @RequestParam(required = false)
            Long seasonId
    ) {

        return ResponseEntity.ok(
                playerTrendService.getPlayerTrends(
                        playerId,
                        competitionId,
                        seasonId
                )
        );
    }
}