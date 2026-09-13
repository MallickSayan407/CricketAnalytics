package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.SeasonAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.SeasonAnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics/seasons")
@RequiredArgsConstructor
public class SeasonAnalyticsController {

    private final SeasonAnalyticsService seasonAnalyticsService;

    @GetMapping("/{seasonId}")
    public ResponseEntity<SeasonAnalyticsResponseDTO> getSeasonAnalytics(
            @PathVariable(name = "seasonId") Long seasonId
    ) {

        return ResponseEntity.ok(
                seasonAnalyticsService.getSeasonAnalytics(
                        seasonId
                )
        );
    }
}