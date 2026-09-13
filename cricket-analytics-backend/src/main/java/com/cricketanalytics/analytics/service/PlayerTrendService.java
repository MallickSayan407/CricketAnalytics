package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.PlayerTrendResponseDTO;

public interface PlayerTrendService {

    PlayerTrendResponseDTO getPlayerTrends(
            Long playerId,
            Long competitionId,
            Long seasonId
    );
}