package com.cricketanalytics.service;

import com.cricketanalytics.dto.CompetitionRequestDTO;
import com.cricketanalytics.dto.CompetitionResponseDTO;
import com.cricketanalytics.entity.Competition;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.CompetitionRepository;
import com.cricketanalytics.service.CompetitionService;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;
import com.cricketanalytics.exception.DuplicateResourceException;
import com.cricketanalytics.exception.ResourceNotFoundException;

@Service
@RequiredArgsConstructor
public class CompetitionServiceImpl implements CompetitionService {

    private final CompetitionRepository competitionRepository;

    @Override
    public CompetitionResponseDTO createCompetition(
            CompetitionRequestDTO request) {

        // Prevent duplicate competition names
        if (competitionRepository.existsByNameIgnoreCase(request.getName())) {
        	throw new DuplicateResourceException(
        	        "Competition already exists: " + request.getName()
        	);
        }

        Competition competition = Competition.builder()
                .name(request.getName())
                .type(request.getType().toUpperCase())
                .format(request.getFormat().toUpperCase())
                .build();

        Competition savedCompetition =
                competitionRepository.save(competition);

        return mapToResponse(savedCompetition);
    }

    @Override
    public List<CompetitionResponseDTO> getAllCompetitions() {

        return competitionRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public CompetitionResponseDTO getCompetitionById(Long id) {

        Competition competition = competitionRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Competition not found with id: " + id
                        )
                );

        return mapToResponse(competition);
    }

    @Override
    public CompetitionResponseDTO updateCompetition(
            Long id,
            CompetitionRequestDTO request) {

        Competition competition = competitionRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Competition not found with id: " + id
                        )
                );

        // Prevent duplicate names when updating
        competitionRepository.findByNameIgnoreCase(request.getName())
                .ifPresent(existingCompetition -> {

                    if (!existingCompetition.getId().equals(id)) {
                    	throw new DuplicateResourceException(
                    	        "Competition already exists: " + request.getName()
                    	);                    }
                });

        competition.setName(request.getName());
        competition.setType(request.getType().toUpperCase());
        competition.setFormat(request.getFormat().toUpperCase());

        Competition updatedCompetition =
                competitionRepository.save(competition);

        return mapToResponse(updatedCompetition);
    }

    @Override
    public void deleteCompetition(Long id) {

        if (!competitionRepository.existsById(id)) {
            throw new ResourceNotFoundException(
                    "Competition not found with id: " + id
            );
        }

        competitionRepository.deleteById(id);
    }

    private CompetitionResponseDTO mapToResponse(
            Competition competition) {

        return CompetitionResponseDTO.builder()
                .id(competition.getId())
                .name(competition.getName())
                .type(competition.getType())
                .format(competition.getFormat())
                .build();
    }
}