package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class SeasonAnalyticsResponseDTO {

    private Long seasonId;

    private String seasonName;

    private Integer startYear;

    private Integer endYear;

    private Long competitionId;

    private String competitionName;

    private String competitionType;

    private String competitionFormat;

    private Integer totalMatches;

    private Integer completedMatches;

    private Integer tiedMatches;

    private Integer noResultMatches;

    private Integer totalRuns;

    private Double averageMatchRuns;

    private Integer highestTeamScore;

    private Integer lowestTeamScore;

    private Integer totalFours;

    private Integer totalSixes;

    private Double averageRunRate;
}