package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class TeamSeasonStandingResponseDTO {

    private Integer rank;

    private Long seasonId;

    private String seasonName;

    private Long competitionId;

    private String competitionName;

    private Long teamId;

    private String teamName;

    private String teamShortName;

    private Integer matches;

    private Integer wins;

    private Integer losses;

    private Integer ties;

    private Integer noResults;

    private Integer points;

    private Double winPercentage;

    private Integer runsScored;

    private Integer ballsFaced;

    private Integer runsConceded;

    private Integer ballsBowled;

    private Double runRate;

    private Double bowlingRate;

    private Double netRunRate;
}