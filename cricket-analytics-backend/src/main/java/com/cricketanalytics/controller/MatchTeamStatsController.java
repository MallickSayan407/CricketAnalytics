package com.cricketanalytics.controller;

import com.cricketanalytics.dto.MatchTeamStatsRequestDTO;
import com.cricketanalytics.dto.MatchTeamStatsResponseDTO;
import com.cricketanalytics.service.MatchTeamStatsService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/match-team-stats")
@RequiredArgsConstructor
public class MatchTeamStatsController {

    private final MatchTeamStatsService statsService;

    @PostMapping
    public ResponseEntity<MatchTeamStatsResponseDTO> createStats(
            @Valid @RequestBody MatchTeamStatsRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(statsService.createStats(request));
    }

    @GetMapping
    public ResponseEntity<List<MatchTeamStatsResponseDTO>>
    getAllStats() {

        return ResponseEntity.ok(
                statsService.getAllStats()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<MatchTeamStatsResponseDTO>
    getStatsById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                statsService.getStatsById(id)
        );
    }

    @GetMapping("/match/{matchId}")
    public ResponseEntity<List<MatchTeamStatsResponseDTO>>
    getStatsByMatch(
            @PathVariable("matchId") Long matchId) {

        return ResponseEntity.ok(
                statsService.getStatsByMatch(matchId)
        );
    }

    @GetMapping("/team/{teamId}")
    public ResponseEntity<List<MatchTeamStatsResponseDTO>>
    getStatsByTeam(
            @PathVariable("teamId") Long teamId) {

        return ResponseEntity.ok(
                statsService.getStatsByTeam(teamId)
        );
    }

    @GetMapping("/match/{matchId}/team/{teamId}")
    public ResponseEntity<MatchTeamStatsResponseDTO>
    getStatsByMatchAndTeam(
            @PathVariable("matchId") Long matchId,
            @PathVariable("teamId") Long teamId) {

        return ResponseEntity.ok(
                statsService.getStatsByMatchAndTeam(
                        matchId,
                        teamId
                )
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<MatchTeamStatsResponseDTO>
    updateStats(
            @PathVariable("id") Long id,
            @Valid @RequestBody MatchTeamStatsRequestDTO request) {

        return ResponseEntity.ok(
                statsService.updateStats(
                        id,
                        request
                )
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStats(
            @PathVariable("id") Long id) {

        statsService.deleteStats(id);

        return ResponseEntity.noContent().build();
    }
}