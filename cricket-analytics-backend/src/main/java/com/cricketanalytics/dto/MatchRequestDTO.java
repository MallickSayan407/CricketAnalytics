package com.cricketanalytics.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
public class MatchRequestDTO {

    @NotNull(message = "Match date is required")
    private LocalDate matchDate;

    @NotBlank(message = "Match status is required")
    private String matchStatus;

    private String tossDecision;

    private String resultDescription;


    @NotNull(message = "Competition ID is required")
    private Long competitionId;

    @NotNull(message = "Season ID is required")
    private Long seasonId;

    @NotNull(message = "Venue ID is required")
    private Long venueId;

    @NotNull(message = "Team 1 ID is required")
    private Long team1Id;

    @NotNull(message = "Team 2 ID is required")
    private Long team2Id;

    private Long tossWinnerTeamId;

    private Long winnerTeamId;
}