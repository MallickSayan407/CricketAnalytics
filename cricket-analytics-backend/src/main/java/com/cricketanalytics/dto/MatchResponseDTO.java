package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.time.LocalDate;

@Getter
@Setter
@Builder
public class MatchResponseDTO {

    private Long id;

    private LocalDate matchDate;

    private String matchStatus;

    private String tossDecision;

    private String resultDescription;


    // Competition

    private Long competitionId;
    private String competitionName;
    private String competitionFormat;


    // Season

    private Long seasonId;
    private String seasonName;


    // Venue

    private Long venueId;
    private String venueName;
    private String venueCity;
    private String venueCountry;


    // Team 1

    private Long team1Id;
    private String team1Name;
    private String team1ShortName;


    // Team 2

    private Long team2Id;
    private String team2Name;
    private String team2ShortName;


    // Toss winner

    private Long tossWinnerTeamId;
    private String tossWinnerTeamName;


    // Match winner

    private Long winnerTeamId;
    private String winnerTeamName;
}