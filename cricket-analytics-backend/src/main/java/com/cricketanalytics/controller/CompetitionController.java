package com.cricketanalytics.controller;

import com.cricketanalytics.dto.CompetitionRequestDTO;
import com.cricketanalytics.dto.CompetitionResponseDTO;
import com.cricketanalytics.service.CompetitionService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/competitions")
@RequiredArgsConstructor
public class CompetitionController {

    private final CompetitionService competitionService;

    // Create a new competition
    @PostMapping
    public ResponseEntity<CompetitionResponseDTO> createCompetition(
            @Valid @RequestBody CompetitionRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(competitionService.createCompetition(request));
    }

    // Get all competitions
    @GetMapping
    public ResponseEntity<List<CompetitionResponseDTO>> getAllCompetitions() {

        return ResponseEntity.ok(
                competitionService.getAllCompetitions()
        );
    }

    // Get competition by ID
    @GetMapping("/{id}")
    public ResponseEntity<CompetitionResponseDTO> getCompetitionById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                competitionService.getCompetitionById(id)
        );
    }

    // Update competition
    @PutMapping("/{id}")
    public ResponseEntity<CompetitionResponseDTO> updateCompetition(
            @PathVariable("id") Long id,
            @Valid @RequestBody CompetitionRequestDTO request) {

        return ResponseEntity.ok(
                competitionService.updateCompetition(id, request)
        );
    }

    // Delete competition
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteCompetition(
            @PathVariable("id") Long id) {

        competitionService.deleteCompetition(id);

        return ResponseEntity.noContent().build();
    }
}