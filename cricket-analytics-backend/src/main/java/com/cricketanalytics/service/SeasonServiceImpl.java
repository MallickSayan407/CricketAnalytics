package com.cricketanalytics.service;

import com.cricketanalytics.dto.SeasonRequestDTO;
import com.cricketanalytics.dto.SeasonResponseDTO;
import com.cricketanalytics.entity.Competition;
import com.cricketanalytics.entity.Season;
import com.cricketanalytics.exception.DuplicateResourceException;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.CompetitionRepository;
import com.cricketanalytics.repository.SeasonRepository;
import com.cricketanalytics.service.SeasonService;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class SeasonServiceImpl implements SeasonService {

    private final SeasonRepository seasonRepository;
    private final CompetitionRepository competitionRepository;

    @Override
    public SeasonResponseDTO createSeason(SeasonRequestDTO request) {

        Competition competition = findCompetitionById(
                request.getCompetitionId()
        );

        if (seasonRepository.existsByNameIgnoreCaseAndCompetition_Id(
                request.getName(),
                request.getCompetitionId())) {

            throw new DuplicateResourceException(
                    "Season already exists for competition: "
                            + request.getName()
            );
        }

        validateYears(request);

        Season season = Season.builder()
                .name(request.getName())
                .startYear(request.getStartYear())
                .endYear(request.getEndYear())
                .competition(competition)
                .build();

        Season savedSeason = seasonRepository.save(season);

        return mapToResponse(savedSeason);
    }

    @Override
    public List<SeasonResponseDTO> getAllSeasons() {

        return seasonRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public SeasonResponseDTO getSeasonById(Long id) {

        Season season = seasonRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Season not found with id: " + id
                        )
                );

        return mapToResponse(season);
    }

    @Override
    public List<SeasonResponseDTO> getSeasonsByCompetition(
            Long competitionId) {

        findCompetitionById(competitionId);

        return seasonRepository
                .findByCompetition_Id(competitionId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public SeasonResponseDTO updateSeason(
            Long id,
            SeasonRequestDTO request) {

        Season season = seasonRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Season not found with id: " + id
                        )
                );

        Competition competition = findCompetitionById(
                request.getCompetitionId()
        );

        validateYears(request);

        seasonRepository
                .findByNameIgnoreCaseAndCompetition_Id(
                        request.getName(),
                        request.getCompetitionId()
                )
                .ifPresent(existingSeason -> {

                    if (!existingSeason.getId().equals(id)) {

                        throw new DuplicateResourceException(
                                "Season already exists for competition: "
                                        + request.getName()
                        );
                    }
                });

        season.setName(request.getName());
        season.setStartYear(request.getStartYear());
        season.setEndYear(request.getEndYear());
        season.setCompetition(competition);

        Season updatedSeason = seasonRepository.save(season);

        return mapToResponse(updatedSeason);
    }

    @Override
    public void deleteSeason(Long id) {

        if (!seasonRepository.existsById(id)) {

            throw new ResourceNotFoundException(
                    "Season not found with id: " + id
            );
        }

        seasonRepository.deleteById(id);
    }

    private Competition findCompetitionById(Long competitionId) {

        return competitionRepository.findById(competitionId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Competition not found with id: "
                                        + competitionId
                        )
                );
    }

    private void validateYears(SeasonRequestDTO request) {

        if (request.getEndYear() != null
                && request.getEndYear() < request.getStartYear()) {

            throw new IllegalArgumentException(
                    "End year cannot be before start year"
            );
        }
    }

    private SeasonResponseDTO mapToResponse(Season season) {

        Competition competition = season.getCompetition();

        return SeasonResponseDTO.builder()
                .id(season.getId())
                .name(season.getName())
                .startYear(season.getStartYear())
                .endYear(season.getEndYear())
                .competitionId(
                        competition != null
                                ? competition.getId()
                                : null
                )
                .competitionName(
                        competition != null
                                ? competition.getName()
                                : null
                )
                .competitionFormat(
                        competition != null
                                ? competition.getFormat()
                                : null
                )
                .build();
    }
}