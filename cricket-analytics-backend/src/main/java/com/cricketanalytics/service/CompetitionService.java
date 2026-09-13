package com.cricketanalytics.service;

import com.cricketanalytics.dto.CompetitionRequestDTO;
import com.cricketanalytics.dto.CompetitionResponseDTO;

import java.util.List;

public interface CompetitionService {

    CompetitionResponseDTO createCompetition(
            CompetitionRequestDTO request);

    List<CompetitionResponseDTO> getAllCompetitions();

    CompetitionResponseDTO getCompetitionById(Long id);

    CompetitionResponseDTO updateCompetition(
            Long id,
            CompetitionRequestDTO request);

    void deleteCompetition(Long id);
}