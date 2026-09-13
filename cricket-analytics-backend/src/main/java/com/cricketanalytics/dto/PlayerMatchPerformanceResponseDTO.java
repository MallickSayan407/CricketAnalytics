package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class PlayerMatchPerformanceResponseDTO {

    private Long id;


    // =========================================================
    // Player
    // =========================================================

    private Long playerId;
    private String playerName;
    private String playerRole;


    // =========================================================
    // Team represented in this match
    // =========================================================

    private Long teamId;
    private String teamName;
    private String teamShortName;


    // =========================================================
    // Match
    // =========================================================

    private Long matchId;
    private String matchDate;

    private String competitionName;
    private String competitionFormat;

    private Long team1Id;
    private String team1Name;
    private String team1ShortName;

    private Long team2Id;
    private String team2Name;
    private String team2ShortName;


    // =========================================================
    // Batting
    // =========================================================

    private Integer battingRuns;
    private Integer ballsFaced;
    private Integer fours;
    private Integer sixes;

    private Double battingStrikeRate;

    private Boolean notOut;


    // =========================================================
    // Bowling
    // =========================================================

    private Integer ballsBowled;

    /*
     * Display representation.
     *
     * Example:
     * 61 balls = 10.1 overs
     */
    private String oversBowled;

    private Integer runsConceded;
    private Integer wickets;

    private Double bowlingEconomy;

    private Integer maidens;
}