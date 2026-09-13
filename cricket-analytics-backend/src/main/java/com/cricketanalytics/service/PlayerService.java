package com.cricketanalytics.service;

import com.cricketanalytics.dto.PlayerRequestDTO;
import com.cricketanalytics.dto.PlayerResponseDTO;

import java.util.List;

public interface PlayerService {

    PlayerResponseDTO createPlayer(PlayerRequestDTO request);

    List<PlayerResponseDTO> getAllPlayers();

    PlayerResponseDTO getPlayerById(Long id);

    List<PlayerResponseDTO> getPlayersByTeam(Long teamId);

    List<PlayerResponseDTO> searchPlayersByName(String name);

    PlayerResponseDTO updatePlayer(Long id, PlayerRequestDTO request);

    void deletePlayer(Long id);
}