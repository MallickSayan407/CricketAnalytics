package com.cricketanalytics.analytics.controller;

import com.cricketanalytics.analytics.dto.LeaderboardResponseDTO;
import com.cricketanalytics.analytics.service.LeaderboardService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/analytics/leaderboard")
@RequiredArgsConstructor
public class LeaderboardController {

    private final LeaderboardService leaderboardService;

    @GetMapping("/runs")
    public ResponseEntity<List<LeaderboardResponseDTO>> getTopRunScorers(
            @RequestParam(name = "competitionId", required = false) Long competitionId,
            @RequestParam(name = "seasonId", required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                leaderboardService.getTopRunScorers(
                        competitionId,
                        seasonId
                )
        );
    }

    @GetMapping("/batting-average")
    public ResponseEntity<List<LeaderboardResponseDTO>> getTopBattingAverage(
            @RequestParam(name = "competitionId", required = false) Long competitionId,
            @RequestParam(name = "seasonId", required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                leaderboardService.getTopBattingAverage(
                        competitionId,
                        seasonId
                )
        );
    }

    @GetMapping("/strike-rate")
    public ResponseEntity<List<LeaderboardResponseDTO>> getTopStrikeRate(
            @RequestParam(name = "competitionId", required = false) Long competitionId,
            @RequestParam(name = "seasonId", required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                leaderboardService.getTopStrikeRate(
                        competitionId,
                        seasonId
                )
        );
    }

    @GetMapping("/centuries")
    public ResponseEntity<List<LeaderboardResponseDTO>> getTopCenturies(
            @RequestParam(name = "competitionId", required = false) Long competitionId,
            @RequestParam(name = "seasonId", required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                leaderboardService.getTopCenturies(
                        competitionId,
                        seasonId
                )
        );
    }

    @GetMapping("/wickets")
    public ResponseEntity<List<LeaderboardResponseDTO>> getTopWickets(
            @RequestParam(name = "competitionId", required = false) Long competitionId,
            @RequestParam(name = "seasonId", required = false) Long seasonId
    ) {

        return ResponseEntity.ok(
                leaderboardService.getTopWickets(
                        competitionId,
                        seasonId
                )
        );
    }
}