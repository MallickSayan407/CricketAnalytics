package com.cricketanalytics.service;

import com.cricketanalytics.dto.PlayerMatchPerformanceRequestDTO;
import com.cricketanalytics.dto.PlayerMatchPerformanceResponseDTO;

import java.util.List;

public interface PlayerMatchPerformanceService {

    PlayerMatchPerformanceResponseDTO createPerformance(
            PlayerMatchPerformanceRequestDTO request
    );

    List<PlayerMatchPerformanceResponseDTO> getAllPerformances();

    PlayerMatchPerformanceResponseDTO getPerformanceById(Long id);

    List<PlayerMatchPerformanceResponseDTO> getPerformancesByPlayer(
            Long playerId
    );

    List<PlayerMatchPerformanceResponseDTO> getPerformancesByMatch(
            Long matchId
    );

    PlayerMatchPerformanceResponseDTO getPerformanceByPlayerAndMatch(
            Long playerId,
            Long matchId
    );

    PlayerMatchPerformanceResponseDTO updatePerformance(
            Long id,
            PlayerMatchPerformanceRequestDTO request
    );

    void deletePerformance(Long id);
}