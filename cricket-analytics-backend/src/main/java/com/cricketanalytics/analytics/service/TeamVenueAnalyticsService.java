package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.TeamVenueAnalyticsResponseDTO;

public interface TeamVenueAnalyticsService {

    TeamVenueAnalyticsResponseDTO getTeamVenueAnalytics(
            Long venueId,
            Long teamId
    );
}