package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.TeamSeasonStandingResponseDTO;
import com.cricketanalytics.analytics.service.TeamSeasonAnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/analytics/seasons")
@RequiredArgsConstructor
public class TeamSeasonAnalyticsController {

    private final TeamSeasonAnalyticsService
            teamSeasonAnalyticsService;

    @GetMapping("/{seasonId}/standings")
    public ResponseEntity<List<TeamSeasonStandingResponseDTO>>
    getSeasonStandings(
            @PathVariable(name = "seasonId") Long seasonId
    ) {

        return ResponseEntity.ok(
                teamSeasonAnalyticsService
                        .getSeasonStandings(seasonId)
        );
    }
}