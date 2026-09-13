package com.cricketanalytics.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class MatchTeamStatsRequestDTO {

    @NotNull(message = "Match ID is required")
    private Long matchId;

    @NotNull(message = "Team ID is required")
    private Long teamId;

    @Min(value = 0, message = "Runs cannot be negative")
    private Integer runs = 0;

    @Min(value = 0, message = "Wickets cannot be negative")
    @Max(value = 10, message = "Wickets cannot exceed 10")
    private Integer wickets = 0;

    @Min(value = 0, message = "Total balls cannot be negative")
    private Integer totalBalls = 0;

    @Min(value = 0, message = "Fours cannot be negative")
    private Integer fours = 0;

    @Min(value = 0, message = "Sixes cannot be negative")
    private Integer sixes = 0;

    @Min(value = 0, message = "Extras cannot be negative")
    private Integer extras = 0;

    @DecimalMin(
            value = "0.0",
            inclusive = true,
            message = "Run rate cannot be negative"
    )
    private Double runRate = 0.0;
}