package com.cricketanalytics.controller;

import com.cricketanalytics.dto.TeamRequestDTO;
import com.cricketanalytics.dto.TeamResponseDTO;
import com.cricketanalytics.service.TeamService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/teams")
@RequiredArgsConstructor
public class TeamController {

    private final TeamService teamService;

    // Create a new team
    @PostMapping
    public ResponseEntity<TeamResponseDTO> createTeam(
            @Valid @RequestBody TeamRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(teamService.createTeam(request));
    }

    // Get all teams
    @GetMapping
    public ResponseEntity<List<TeamResponseDTO>> getAllTeams() {

        return ResponseEntity.ok(teamService.getAllTeams());
    }

    // Get team by ID
    @GetMapping("/{id}")
    public ResponseEntity<TeamResponseDTO> getTeamById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(teamService.getTeamById(id));
    }

    // Update team
    @PutMapping("/{id}")
    public ResponseEntity<TeamResponseDTO> updateTeam(
            @PathVariable("id") Long id,
            @Valid @RequestBody TeamRequestDTO request) {

        return ResponseEntity.ok(teamService.updateTeam(id, request));
    }

    // Delete team
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteTeam(
            @PathVariable("id") Long id) {

        teamService.deleteTeam(id);

        return ResponseEntity.noContent().build();
    }
}