package com.cricketanalytics.controller;

import com.cricketanalytics.dto.SeasonRequestDTO;
import com.cricketanalytics.dto.SeasonResponseDTO;
import com.cricketanalytics.service.SeasonService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/seasons")
@RequiredArgsConstructor
public class SeasonController {

    private final SeasonService seasonService;

    @PostMapping
    public ResponseEntity<SeasonResponseDTO> createSeason(
            @Valid @RequestBody SeasonRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(seasonService.createSeason(request));
    }

    @GetMapping
    public ResponseEntity<List<SeasonResponseDTO>> getAllSeasons() {

        return ResponseEntity.ok(
                seasonService.getAllSeasons()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<SeasonResponseDTO> getSeasonById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                seasonService.getSeasonById(id)
        );
    }

    @GetMapping("/competition/{competitionId}")
    public ResponseEntity<List<SeasonResponseDTO>>
    getSeasonsByCompetition(
            @PathVariable("competitionId") Long competitionId) {

        return ResponseEntity.ok(
                seasonService.getSeasonsByCompetition(
                        competitionId
                )
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<SeasonResponseDTO> updateSeason(
            @PathVariable("id") Long id,
            @Valid @RequestBody SeasonRequestDTO request) {

        return ResponseEntity.ok(
                seasonService.updateSeason(id, request)
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteSeason(
            @PathVariable("id") Long id) {

        seasonService.deleteSeason(id);

        return ResponseEntity.noContent().build();
    }
}