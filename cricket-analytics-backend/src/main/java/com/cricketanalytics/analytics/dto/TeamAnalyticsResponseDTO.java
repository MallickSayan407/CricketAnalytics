package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class TeamAnalyticsResponseDTO {

    private Long teamId;

    private String teamName;

    private String teamShortName;

    private MatchStats matchStats;

    private Performance performance;


    @Getter
    @Setter
    @Builder
    public static class MatchStats {

        private Integer matches;

        private Integer wins;

        private Integer losses;

        private Integer ties;

        private Integer noResults;

        private Double winPercentage;
    }


    @Getter
    @Setter
    @Builder
    public static class Performance {

        private Integer runsScored;

        private Double averageRuns;

        private Integer wicketsLost;

        private Double averageRunRate;

        private Integer runsConceded;

        private Double bowlingRate;

        private Double netRunRate;

        private Integer fours;

        private Integer sixes;
    }
}