package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.PlayerAnalyticsResponseDTO;

public interface PlayerAnalyticsService {

    PlayerAnalyticsResponseDTO getPlayerAnalytics(
            Long playerId,
            Long competitionId,
            Long seasonId
    );
}