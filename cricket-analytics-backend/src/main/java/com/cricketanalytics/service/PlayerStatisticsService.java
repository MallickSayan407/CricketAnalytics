package com.cricketanalytics.service;

import com.cricketanalytics.dto.PlayerStatisticsRequestDTO;
import com.cricketanalytics.dto.PlayerStatisticsResponseDTO;

import java.util.List;

public interface PlayerStatisticsService {

    PlayerStatisticsResponseDTO createStatistics(
            PlayerStatisticsRequestDTO request
    );

    List<PlayerStatisticsResponseDTO> getAllStatistics();

    PlayerStatisticsResponseDTO getStatisticsById(Long id);

    PlayerStatisticsResponseDTO getPlayerStatistics(
            Long playerId,
            Long competitionId,
            Long seasonId
    );

    List<PlayerStatisticsResponseDTO> getStatisticsByPlayer(
            Long playerId
    );

    List<PlayerStatisticsResponseDTO> getStatisticsByCompetition(
            Long competitionId
    );

    List<PlayerStatisticsResponseDTO> getStatisticsBySeason(
            Long seasonId
    );

    PlayerStatisticsResponseDTO updateStatistics(
            Long id,
            PlayerStatisticsRequestDTO request
    );

    void deleteStatistics(Long id);
}