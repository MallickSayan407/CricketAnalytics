package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class PlayerComparisonResponseDTO {

    private List<PlayerComparison> players;


    @Getter
    @Setter
    @Builder
    public static class PlayerComparison {

        private Long playerId;

        private String playerName;

        private String teamName;

        private String teamShortName;

        private String role;

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
}