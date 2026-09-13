package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.TeamVenueAnalyticsResponseDTO;
import com.cricketanalytics.analytics.dto.VenueAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.TeamVenueAnalyticsService;
import com.cricketanalytics.analytics.service.VenueAnalyticsService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/analytics/venues")
@RequiredArgsConstructor
public class VenueAnalyticsController {

    private final VenueAnalyticsService venueAnalyticsService;

    private final TeamVenueAnalyticsService teamVenueAnalyticsService;

    @GetMapping("/{venueId}")
    public ResponseEntity<VenueAnalyticsResponseDTO> getVenueAnalytics(
            @PathVariable(name = "venueId") Long venueId
    ) {

        return ResponseEntity.ok(
                venueAnalyticsService.getVenueAnalytics(
                        venueId
                )
        );
    }

    @GetMapping("/{venueId}/teams/{teamId}")
    public ResponseEntity<TeamVenueAnalyticsResponseDTO>
    getTeamVenueAnalytics(
            @PathVariable(name = "venueId") Long venueId,
            @PathVariable(name = "teamId") Long teamId
    ) {

        return ResponseEntity.ok(
                teamVenueAnalyticsService.getTeamVenueAnalytics(
                        venueId,
                        teamId
                )
        );
    }
}