package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.MatchAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.MatchAnalyticsService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics/matches")
@RequiredArgsConstructor
public class MatchAnalyticsController {

    private final MatchAnalyticsService matchAnalyticsService;


    @GetMapping("/{matchId}")
    public ResponseEntity<MatchAnalyticsResponseDTO>
    getMatchAnalytics(
            @PathVariable("matchId") Long matchId) {

        return ResponseEntity.ok(
                matchAnalyticsService
                        .getMatchAnalytics(matchId)
        );
    }
}