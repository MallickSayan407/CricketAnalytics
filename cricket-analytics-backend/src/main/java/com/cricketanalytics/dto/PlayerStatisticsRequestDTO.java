package com.cricketanalytics.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PlayerStatisticsRequestDTO {

    @NotNull(message = "Player ID is required")
    private Long playerId;

    @NotNull(message = "Competition ID is required")
    private Long competitionId;

    @NotNull(message = "Season ID is required")
    private Long seasonId;

    // =========================
    // Batting
    // =========================

    @Min(value = 0, message = "Matches cannot be negative")
    private Integer matches = 0;

    @Min(value = 0, message = "Batting innings cannot be negative")
    private Integer battingInnings = 0;

    @Min(value = 0, message = "Runs cannot be negative")
    private Integer runs = 0;

    @Min(value = 0, message = "Balls faced cannot be negative")
    private Integer ballsFaced = 0;

    @Min(value = 0, message = "Highest score cannot be negative")
    private Integer highestScore = 0;

    @Min(value = 0, message = "Not outs cannot be negative")
    private Integer notOuts = 0;

    @Min(value = 0, message = "Fours cannot be negative")
    private Integer fours = 0;

    @Min(value = 0, message = "Sixes cannot be negative")
    private Integer sixes = 0;

    @Min(value = 0, message = "Fifties cannot be negative")
    private Integer fifties = 0;

    @Min(value = 0, message = "Centuries cannot be negative")
    private Integer centuries = 0;

    // =========================
    // Derived batting statistics
    // =========================

    @DecimalMin(
            value = "0.0",
            inclusive = true,
            message = "Batting average cannot be negative"
    )
    private Double battingAverage = 0.0;

    @DecimalMin(
            value = "0.0",
            inclusive = true,
            message = "Strike rate cannot be negative"
    )
    private Double strikeRate = 0.0;

    // =========================
    // Bowling
    // =========================

    @Min(value = 0, message = "Bowling innings cannot be negative")
    private Integer bowlingInnings = 0;

    @Min(value = 0, message = "Balls bowled cannot be negative")
    private Integer ballsBowled = 0;

    @Min(value = 0, message = "Wickets cannot be negative")
    private Integer wickets = 0;

    @Min(value = 0, message = "Runs conceded cannot be negative")
    private Integer runsConceded = 0;

    // =========================
    // Derived bowling statistics
    // =========================

    @DecimalMin(
            value = "0.0",
            inclusive = true,
            message = "Economy cannot be negative"
    )
    private Double economy = 0.0;

    @DecimalMin(
            value = "0.0",
            inclusive = true,
            message = "Bowling average cannot be negative"
    )
    private Double bowlingAverage = 0.0;

    @Min(value = 0, message = "Best bowling wickets cannot be negative")
    private Integer bestBowlingWickets = 0;

    @Min(value = 0, message = "Five wicket hauls cannot be negative")
    private Integer fiveWicketHauls = 0;
}