package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class PlayerAnalyticsResponseDTO {

    private Long playerId;

    private String playerName;

    private String teamName;

    private String teamShortName;

    private CareerStats careerStats;

    private MatchPerformanceSummary matchPerformance;

    @Getter
    @Setter
    @Builder
    public static class CareerStats {

        private Integer matches;

        private Integer runs;

        private Integer highestScore;

        private Integer fifties;

        private Integer centuries;

        private Integer notOuts;

        private Double battingAverage;

        private Double strikeRate;

        private Integer wickets;

        private Integer runsConceded;

        private Double economy;

        private Double bowlingAverage;

        private Integer fiveWicketHauls;
    }

    @Getter
    @Setter
    @Builder
    public static class MatchPerformanceSummary {

        private Integer matches;

        private Integer runs;

        private Integer ballsFaced;

        private Integer fours;

        private Integer sixes;

        private Double averageStrikeRate;

        private Integer wickets;

        private Integer runsConceded;

        private Double averageEconomy;
    }
}