package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class PlayerStatisticsResponseDTO {

    private Long id;

    // =========================
    // Player / competition
    // =========================

    private Long playerId;
    private String playerName;

    private Long competitionId;
    private String competitionName;
    private String competitionType;
    private String competitionFormat;

    private Long seasonId;
    private String seasonName;

    // =========================
    // Batting
    // =========================

    private Integer matches;
    private Integer battingInnings;
    private Integer runs;
    private Integer ballsFaced;
    private Integer highestScore;
    private Integer notOuts;
    private Integer fours;
    private Integer sixes;
    private Integer fifties;
    private Integer centuries;

    private Double battingAverage;
    private Double strikeRate;

    // =========================
    // Bowling
    // =========================

    private Integer bowlingInnings;
    private Integer ballsBowled;
    private Integer wickets;
    private Integer runsConceded;

    private Double economy;
    private Double bowlingAverage;

    private Integer bestBowlingWickets;
    private Integer fiveWicketHauls;
}