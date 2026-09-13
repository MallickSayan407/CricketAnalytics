package com.cricketanalytics.service;

import com.cricketanalytics.dto.TeamRequestDTO;
import com.cricketanalytics.dto.TeamResponseDTO;

import java.util.List;

public interface TeamService {

    TeamResponseDTO createTeam(TeamRequestDTO request);

    List<TeamResponseDTO> getAllTeams();

    TeamResponseDTO getTeamById(Long id);

    TeamResponseDTO updateTeam(Long id, TeamRequestDTO request);

    void deleteTeam(Long id);
}