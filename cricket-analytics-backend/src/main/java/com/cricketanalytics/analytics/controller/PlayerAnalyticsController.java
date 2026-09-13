package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.PlayerAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.PlayerAnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics/players")
@RequiredArgsConstructor
public class PlayerAnalyticsController {

    private final PlayerAnalyticsService playerAnalyticsService;

    @GetMapping("/{playerId}")
    public ResponseEntity<PlayerAnalyticsResponseDTO> getPlayerAnalytics(
            @PathVariable Long playerId,
            @RequestParam(required = false) Long competitionId,
            @RequestParam(required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                playerAnalyticsService.getPlayerAnalytics(
                        playerId,
                        competitionId,
                        seasonId
                )
        );
    }
}