package com.cricketanalytics.controller;

import com.cricketanalytics.dto.MatchRequestDTO;
import com.cricketanalytics.dto.MatchResponseDTO;
import com.cricketanalytics.service.MatchService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/matches")
@RequiredArgsConstructor
public class MatchController {

    private final MatchService matchService;

    @PostMapping
    public ResponseEntity<MatchResponseDTO> createMatch(
            @Valid @RequestBody MatchRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(matchService.createMatch(request));
    }

    @GetMapping
    public ResponseEntity<List<MatchResponseDTO>> getAllMatches() {

        return ResponseEntity.ok(
                matchService.getAllMatches()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<MatchResponseDTO> getMatchById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                matchService.getMatchById(id)
        );
    }

    @GetMapping("/competition/{competitionId}")
    public ResponseEntity<List<MatchResponseDTO>>
    getMatchesByCompetition(
            @PathVariable("competitionId") Long competitionId) {

        return ResponseEntity.ok(
                matchService.getMatchesByCompetition(
                        competitionId
                )
        );
    }

    @GetMapping("/season/{seasonId}")
    public ResponseEntity<List<MatchResponseDTO>>
    getMatchesBySeason(
            @PathVariable("seasonId") Long seasonId) {

        return ResponseEntity.ok(
                matchService.getMatchesBySeason(
                        seasonId
                )
        );
    }

    @GetMapping("/venue/{venueId}")
    public ResponseEntity<List<MatchResponseDTO>>
    getMatchesByVenue(
            @PathVariable("venueId") Long venueId) {

        return ResponseEntity.ok(
                matchService.getMatchesByVenue(venueId)
        );
    }

    @GetMapping("/team/{teamId}")
    public ResponseEntity<List<MatchResponseDTO>>
    getMatchesByTeam(
            @PathVariable("teamId") Long teamId) {

        return ResponseEntity.ok(
                matchService.getMatchesByTeam(teamId)
        );
    }

    @GetMapping("/date-range")
    public ResponseEntity<List<MatchResponseDTO>>
    getMatchesBetweenDates(

            @RequestParam("startDate")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate startDate,

            @RequestParam("endDate")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate endDate) {

        return ResponseEntity.ok(
                matchService.getMatchesBetweenDates(
                        startDate,
                        endDate
                )
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<MatchResponseDTO> updateMatch(
            @PathVariable("id") Long id,
            @Valid @RequestBody MatchRequestDTO request) {

        return ResponseEntity.ok(
                matchService.updateMatch(id, request)
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteMatch(
            @PathVariable("id") Long id) {

        matchService.deleteMatch(id);

        return ResponseEntity.noContent().build();
    }
}