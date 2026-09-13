package com.cricketanalytics.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PlayerMatchPerformanceRequestDTO {

    @NotNull(message = "Player ID is required")
    private Long playerId;

    @NotNull(message = "Match ID is required")
    private Long matchId;

    /**
     * Team represented by the player in this particular match.
     *
     * This must be one of the two teams participating in the match.
     */
    @NotNull(message = "Team ID is required")
    private Long teamId;


    // =========================================================
    // Batting
    // =========================================================

    @Min(value = 0, message = "Batting runs cannot be negative")
    private Integer battingRuns = 0;

    @Min(value = 0, message = "Balls faced cannot be negative")
    private Integer ballsFaced = 0;

    @Min(value = 0, message = "Fours cannot be negative")
    private Integer fours = 0;

    @Min(value = 0, message = "Sixes cannot be negative")
    private Integer sixes = 0;

    /*
     * Calculated by the backend.
     */
    private Boolean notOut = false;


    // =========================================================
    // Bowling
    // =========================================================

    @Min(value = 0, message = "Balls bowled cannot be negative")
    private Integer ballsBowled = 0;

    @Min(value = 0, message = "Runs conceded cannot be negative")
    private Integer runsConceded = 0;

    @Min(value = 0, message = "Wickets cannot be negative")
    private Integer wickets = 0;

    @Min(value = 0, message = "Maidens cannot be negative")
    private Integer maidens = 0;

    /*
     * Calculated by the backend.
     */
}