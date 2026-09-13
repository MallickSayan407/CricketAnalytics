package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.TeamAnalyticsResponseDTO;

public interface TeamAnalyticsService {

    TeamAnalyticsResponseDTO getTeamAnalytics(
            Long teamId,
            Long competitionId,
            Long seasonId
    );
}