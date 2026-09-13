package com.cricketanalytics.controller;

import com.cricketanalytics.dto.PlayerRequestDTO;
import com.cricketanalytics.dto.PlayerResponseDTO;
import com.cricketanalytics.service.PlayerService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/players")
@RequiredArgsConstructor
public class PlayerController {

    private final PlayerService playerService;

    // Create a new player
    @PostMapping
    public ResponseEntity<PlayerResponseDTO> createPlayer(
            @Valid @RequestBody PlayerRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(playerService.createPlayer(request));
    }

    // Get all players
    @GetMapping
    public ResponseEntity<List<PlayerResponseDTO>> getAllPlayers() {

        return ResponseEntity.ok(playerService.getAllPlayers());
    }

    // Get player by ID
    @GetMapping("/{id}")
    public ResponseEntity<PlayerResponseDTO> getPlayerById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(playerService.getPlayerById(id));
    }

    // Get all players belonging to a team
    @GetMapping("/team/{teamId}")
    public ResponseEntity<List<PlayerResponseDTO>> getPlayersByTeam(
            @PathVariable("teamId") Long teamId) {

        return ResponseEntity.ok(
                playerService.getPlayersByTeam(teamId)
        );
    }

    // Search players by name
    @GetMapping("/search")
    public ResponseEntity<List<PlayerResponseDTO>> searchPlayers(
            @RequestParam("name") String name) {

        return ResponseEntity.ok(
                playerService.searchPlayersByName(name)
        );
    }

    // Update player
    @PutMapping("/{id}")
    public ResponseEntity<PlayerResponseDTO> updatePlayer(
            @PathVariable("id") Long id,
            @Valid @RequestBody PlayerRequestDTO request) {

        return ResponseEntity.ok(
                playerService.updatePlayer(id, request)
        );
    }

    // Delete player
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deletePlayer(
            @PathVariable("id") Long id) {

        playerService.deletePlayer(id);

        return ResponseEntity.noContent().build();
    }
}