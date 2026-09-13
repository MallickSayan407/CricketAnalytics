package com.cricketanalytics.service;

import com.cricketanalytics.dto.MatchTeamStatsRequestDTO;
import com.cricketanalytics.dto.MatchTeamStatsResponseDTO;

import java.util.List;

public interface MatchTeamStatsService {

    MatchTeamStatsResponseDTO createStats(
            MatchTeamStatsRequestDTO request
    );

    List<MatchTeamStatsResponseDTO> getAllStats();

    MatchTeamStatsResponseDTO getStatsById(Long id);

    List<MatchTeamStatsResponseDTO> getStatsByMatch(
            Long matchId
    );

    List<MatchTeamStatsResponseDTO> getStatsByTeam(
            Long teamId
    );

    MatchTeamStatsResponseDTO getStatsByMatchAndTeam(
            Long matchId,
            Long teamId
    );

    MatchTeamStatsResponseDTO updateStats(
            Long id,
            MatchTeamStatsRequestDTO request
    );

    void deleteStats(Long id);
}