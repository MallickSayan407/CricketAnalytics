package com.cricketanalytics.service;

import com.cricketanalytics.dto.MatchRequestDTO;
import com.cricketanalytics.dto.MatchResponseDTO;

import java.time.LocalDate;
import java.util.List;

public interface MatchService {

    MatchResponseDTO createMatch(MatchRequestDTO request);

    List<MatchResponseDTO> getAllMatches();

    MatchResponseDTO getMatchById(Long id);

    List<MatchResponseDTO> getMatchesByCompetition(
            Long competitionId
    );

    List<MatchResponseDTO> getMatchesBySeason(
            Long seasonId
    );

    List<MatchResponseDTO> getMatchesByVenue(
            Long venueId
    );

    List<MatchResponseDTO> getMatchesByTeam(
            Long teamId
    );

    List<MatchResponseDTO> getMatchesBetweenDates(
            LocalDate startDate,
            LocalDate endDate
    );

    MatchResponseDTO updateMatch(
            Long id,
            MatchRequestDTO request
    );

    void deleteMatch(Long id);
}