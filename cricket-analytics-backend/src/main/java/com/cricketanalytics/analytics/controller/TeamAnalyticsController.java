package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.TeamAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.TeamAnalyticsService;

import lombok.RequiredArgsConstructor;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics/teams")
@RequiredArgsConstructor
public class TeamAnalyticsController {

    private final TeamAnalyticsService teamAnalyticsService;

    @GetMapping("/{teamId}")
    public ResponseEntity<TeamAnalyticsResponseDTO> getTeamAnalytics(
            @PathVariable Long teamId,
            @RequestParam(required = false) Long competitionId,
            @RequestParam(required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                teamAnalyticsService.getTeamAnalytics(
                        teamId,
                        competitionId,
                        seasonId
                )
        );
    }
}