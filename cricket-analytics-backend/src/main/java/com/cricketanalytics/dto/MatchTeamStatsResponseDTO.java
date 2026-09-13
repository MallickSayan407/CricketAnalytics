package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class MatchTeamStatsResponseDTO {

    private Long id;

    private Long matchId;
    private String matchDate;

    private Long teamId;
    private String teamName;
    private String teamShortName;

    private Integer runs;
    private Integer wickets;

    private Integer totalBalls;

    /*
     * Display value.
     *
     * Example:
     * 272 balls → 45.2 overs
     */
    private String overs;

    private Integer fours;
    private Integer sixes;
    private Integer extras;
    private Double runRate;
}