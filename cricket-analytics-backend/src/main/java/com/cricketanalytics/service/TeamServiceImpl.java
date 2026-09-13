package com.cricketanalytics.service;

import com.cricketanalytics.dto.TeamRequestDTO;
import com.cricketanalytics.dto.TeamResponseDTO;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.TeamRepository;
import com.cricketanalytics.service.TeamService;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class TeamServiceImpl implements TeamService {

    private final TeamRepository teamRepository;

    @Override
    public TeamResponseDTO createTeam(TeamRequestDTO request) {

        Team team = Team.builder()
                .name(request.getName())
                .shortName(request.getShortName().toUpperCase())
                .country(request.getCountry())
                .logoUrl(request.getLogoUrl())
                .build();

        Team savedTeam = teamRepository.save(team);

        return mapToResponse(savedTeam);
    }

    @Override
    public List<TeamResponseDTO> getAllTeams() {

        return teamRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public TeamResponseDTO getTeamById(Long id) {

        Team team = teamRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: " + id
                        )
                );

        return mapToResponse(team);
    }

    @Override
    public TeamResponseDTO updateTeam(
            Long id,
            TeamRequestDTO request) {

        Team team = teamRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: " + id
                        )
                );

        team.setName(request.getName());
        team.setShortName(request.getShortName().toUpperCase());
        team.setCountry(request.getCountry());
        team.setLogoUrl(request.getLogoUrl());

        Team updatedTeam = teamRepository.save(team);

        return mapToResponse(updatedTeam);
    }

    @Override
    public void deleteTeam(Long id) {

        if (!teamRepository.existsById(id)) {
            throw new ResourceNotFoundException(
                    "Team not found with id: " + id
            );
        }

        teamRepository.deleteById(id);
    }

    private TeamResponseDTO mapToResponse(Team team) {

        return TeamResponseDTO.builder()
                .id(team.getId())
                .name(team.getName())
                .shortName(team.getShortName())
                .country(team.getCountry())
                .logoUrl(team.getLogoUrl())
                .build();
    }
}