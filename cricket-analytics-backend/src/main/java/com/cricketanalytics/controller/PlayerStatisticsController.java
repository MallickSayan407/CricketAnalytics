package com.cricketanalytics.controller;

import com.cricketanalytics.dto.PlayerStatisticsRequestDTO;
import com.cricketanalytics.dto.PlayerStatisticsResponseDTO;
import com.cricketanalytics.service.PlayerStatisticsService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/statistics")
@RequiredArgsConstructor
public class PlayerStatisticsController {

    private final PlayerStatisticsService statisticsService;

    @PostMapping
    public ResponseEntity<PlayerStatisticsResponseDTO> createStatistics(
            @Valid @RequestBody PlayerStatisticsRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(statisticsService.createStatistics(request));
    }

    @GetMapping
    public ResponseEntity<List<PlayerStatisticsResponseDTO>>
    getAllStatistics() {

        return ResponseEntity.ok(
                statisticsService.getAllStatistics()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<PlayerStatisticsResponseDTO>
    getStatisticsById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                statisticsService.getStatisticsById(id)
        );
    }

    @GetMapping("/player/{playerId}")
    public ResponseEntity<List<PlayerStatisticsResponseDTO>>
    getStatisticsByPlayer(
            @PathVariable("playerId") Long playerId) {

        return ResponseEntity.ok(
                statisticsService.getStatisticsByPlayer(playerId)
        );
    }

    @GetMapping("/competition/{competitionId}")
    public ResponseEntity<List<PlayerStatisticsResponseDTO>>
    getStatisticsByCompetition(
            @PathVariable("competitionId") Long competitionId) {

        return ResponseEntity.ok(
                statisticsService.getStatisticsByCompetition(
                        competitionId
                )
        );
    }

    @GetMapping("/season/{seasonId}")
    public ResponseEntity<List<PlayerStatisticsResponseDTO>>
    getStatisticsBySeason(
            @PathVariable("seasonId") Long seasonId) {

        return ResponseEntity.ok(
                statisticsService.getStatisticsBySeason(seasonId)
        );
    }

    @GetMapping("/player/{playerId}/competition/{competitionId}/season/{seasonId}")
    public ResponseEntity<PlayerStatisticsResponseDTO>
    getPlayerStatistics(
            @PathVariable("playerId") Long playerId,
            @PathVariable("competitionId") Long competitionId,
            @PathVariable("seasonId") Long seasonId) {

        return ResponseEntity.ok(
                statisticsService.getPlayerStatistics(
                        playerId,
                        competitionId,
                        seasonId
                )
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<PlayerStatisticsResponseDTO>
    updateStatistics(
            @PathVariable("id") Long id,
            @Valid @RequestBody PlayerStatisticsRequestDTO request) {

        return ResponseEntity.ok(
                statisticsService.updateStatistics(
                        id,
                        request
                )
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteStatistics(
            @PathVariable("id") Long id) {

        statisticsService.deleteStatistics(id);

        return ResponseEntity.noContent().build();
    }
}