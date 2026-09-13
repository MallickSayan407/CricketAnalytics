package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.PlayerComparisonResponseDTO;
import com.cricketanalytics.analytics.service.PlayerComparisonService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/analytics/players")
@RequiredArgsConstructor
public class PlayerComparisonController {

    private final PlayerComparisonService playerComparisonService;

    @GetMapping("/compare")
    public ResponseEntity<PlayerComparisonResponseDTO> comparePlayers(
            @RequestParam("playerIds") List<Long> playerIds,
            @RequestParam(required = false) Long competitionId,
            @RequestParam(required = false) Long seasonId) {

        return ResponseEntity.ok(
                playerComparisonService.comparePlayers(
                        playerIds,
                        competitionId,
                        seasonId
                )
        );
    }
}