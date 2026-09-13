package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.LeaderboardResponseDTO;

import java.util.List;

public interface LeaderboardService {

    List<LeaderboardResponseDTO> getTopRunScorers(
            Long competitionId,
            Long seasonId
    );

    List<LeaderboardResponseDTO> getTopBattingAverage(
            Long competitionId,
            Long seasonId
    );

    List<LeaderboardResponseDTO> getTopStrikeRate(
            Long competitionId,
            Long seasonId
    );

    List<LeaderboardResponseDTO> getTopCenturies(
            Long competitionId,
            Long seasonId
    );

    List<LeaderboardResponseDTO> getTopWickets(
            Long competitionId,
            Long seasonId
    );
}