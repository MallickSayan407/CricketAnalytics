package com.cricketanalytics.controller;

import com.cricketanalytics.dto.PlayerMatchPerformanceRequestDTO;
import com.cricketanalytics.dto.PlayerMatchPerformanceResponseDTO;
import com.cricketanalytics.service.PlayerMatchPerformanceService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/player-match-performance")
@RequiredArgsConstructor
public class PlayerMatchPerformanceController {

    private final PlayerMatchPerformanceService performanceService;

    @PostMapping
    public ResponseEntity<PlayerMatchPerformanceResponseDTO> createPerformance(
            @Valid @RequestBody PlayerMatchPerformanceRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(performanceService.createPerformance(request));
    }

    @GetMapping
    public ResponseEntity<List<PlayerMatchPerformanceResponseDTO>>
    getAllPerformances() {

        return ResponseEntity.ok(
                performanceService.getAllPerformances()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<PlayerMatchPerformanceResponseDTO>
    getPerformanceById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                performanceService.getPerformanceById(id)
        );
    }

    @GetMapping("/player/{playerId}")
    public ResponseEntity<List<PlayerMatchPerformanceResponseDTO>>
    getPerformancesByPlayer(
            @PathVariable("playerId") Long playerId) {

        return ResponseEntity.ok(
                performanceService.getPerformancesByPlayer(playerId)
        );
    }

    @GetMapping("/match/{matchId}")
    public ResponseEntity<List<PlayerMatchPerformanceResponseDTO>>
    getPerformancesByMatch(
            @PathVariable("matchId") Long matchId) {

        return ResponseEntity.ok(
                performanceService.getPerformancesByMatch(matchId)
        );
    }

    @GetMapping("/player/{playerId}/match/{matchId}")
    public ResponseEntity<PlayerMatchPerformanceResponseDTO>
    getPerformanceByPlayerAndMatch(
            @PathVariable("playerId") Long playerId,
            @PathVariable("matchId") Long matchId) {

        return ResponseEntity.ok(
                performanceService
                        .getPerformanceByPlayerAndMatch(
                                playerId,
                                matchId
                        )
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<PlayerMatchPerformanceResponseDTO>
    updatePerformance(
            @PathVariable("id") Long id,
            @Valid @RequestBody PlayerMatchPerformanceRequestDTO request) {

        return ResponseEntity.ok(
                performanceService.updatePerformance(
                        id,
                        request
                )
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deletePerformance(
            @PathVariable("id") Long id) {

        performanceService.deletePerformance(id);

        return ResponseEntity.noContent().build();
    }
}