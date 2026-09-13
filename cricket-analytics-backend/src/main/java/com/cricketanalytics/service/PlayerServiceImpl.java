package com.cricketanalytics.service;

import com.cricketanalytics.dto.PlayerRequestDTO;
import com.cricketanalytics.dto.PlayerResponseDTO;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.PlayerRepository;
import com.cricketanalytics.repository.TeamRepository;
import com.cricketanalytics.service.PlayerService;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PlayerServiceImpl implements PlayerService {

    private final PlayerRepository playerRepository;
    private final TeamRepository teamRepository;

    @Override
    public PlayerResponseDTO createPlayer(PlayerRequestDTO request) {

        Team team = findTeamById(request.getTeamId());

        Player player = Player.builder()
                .name(request.getName())
                .externalId(request.getExternalId())
                .role(request.getRole())
                .battingStyle(request.getBattingStyle())
                .bowlingStyle(request.getBowlingStyle())
                .avatarUrl(request.getAvatarUrl())
                .team(team)
                .build();

        Player savedPlayer = playerRepository.save(player);

        return mapToResponse(savedPlayer);
    }

    @Override
    public List<PlayerResponseDTO> getAllPlayers() {

        return playerRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public PlayerResponseDTO getPlayerById(Long id) {

        Player player = playerRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Player not found with id: " + id
                        )
                );

        return mapToResponse(player);
    }

    @Override
    public List<PlayerResponseDTO> getPlayersByTeam(Long teamId) {

        // Make sure the team exists before searching for its players
        findTeamById(teamId);

        return playerRepository.findByTeam_Id(teamId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<PlayerResponseDTO> searchPlayersByName(String name) {

        return playerRepository.findByNameContainingIgnoreCase(name)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public PlayerResponseDTO updatePlayer(
            Long id,
            PlayerRequestDTO request) {

        Player player = playerRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Player not found with id: " + id
                        )
                );

        Team team = findTeamById(request.getTeamId());

        player.setName(request.getName());
        player.setExternalId(request.getExternalId());
        player.setRole(request.getRole());
        player.setBattingStyle(request.getBattingStyle());
        player.setBowlingStyle(request.getBowlingStyle());
        player.setAvatarUrl(request.getAvatarUrl());
        player.setTeam(team);

        Player updatedPlayer = playerRepository.save(player);

        return mapToResponse(updatedPlayer);
    }

    @Override
    public void deletePlayer(Long id) {

        if (!playerRepository.existsById(id)) {
            throw new ResourceNotFoundException(
                    "Player not found with id: " + id
            );
        }

        playerRepository.deleteById(id);
    }

    private Team findTeamById(Long teamId) {

        if (teamId == null) {
            throw new ResourceNotFoundException(
                    "Team ID is required"
            );
        }

        return teamRepository.findById(teamId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: " + teamId
                        )
                );
    }

    private PlayerResponseDTO mapToResponse(Player player) {

        Team team = player.getTeam();

        return PlayerResponseDTO.builder()
                .id(player.getId())
                .name(player.getName())
                .externalId(player.getExternalId())
                .role(player.getRole())
                .battingStyle(player.getBattingStyle())
                .bowlingStyle(player.getBowlingStyle())
                .avatarUrl(player.getAvatarUrl())
                .teamId(team != null ? team.getId() : null)
                .teamName(team != null ? team.getName() : null)
                .teamShortName(team != null ? team.getShortName() : null)
                .build();
    }
}