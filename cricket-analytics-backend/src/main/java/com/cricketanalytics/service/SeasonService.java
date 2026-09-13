package com.cricketanalytics.service;

import com.cricketanalytics.dto.SeasonRequestDTO;
import com.cricketanalytics.dto.SeasonResponseDTO;

import java.util.List;

public interface SeasonService {

    SeasonResponseDTO createSeason(SeasonRequestDTO request);

    List<SeasonResponseDTO> getAllSeasons();

    SeasonResponseDTO getSeasonById(Long id);

    List<SeasonResponseDTO> getSeasonsByCompetition(Long competitionId);

    SeasonResponseDTO updateSeason(Long id, SeasonRequestDTO request);

    void deleteSeason(Long id);
}