package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class LeaderboardResponseDTO {

    private Integer rank;

    private Long playerId;

    private String playerName;

    private String playerRole;

    private String teamName;

    private String teamShortName;

    private Integer matches;

    private Integer runs;

    private Double battingAverage;

    private Double strikeRate;

    private Integer centuries;

    private Integer fifties;

    private Integer wickets;

    private Double bowlingAverage;

    private Double economy;
}