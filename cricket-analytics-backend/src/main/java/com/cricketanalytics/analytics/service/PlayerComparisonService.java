package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.PlayerComparisonResponseDTO;

import java.util.List;

public interface PlayerComparisonService {

    PlayerComparisonResponseDTO comparePlayers(
            List<Long> playerIds,
            Long competitionId,
            Long seasonId
    );
}