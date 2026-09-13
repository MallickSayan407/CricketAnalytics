package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class PlayerTrendResponseDTO {

    private Long playerId;

    private String playerName;

    private RecentForm recentForm;

    private List<MatchTrend> matchTrend;


    @Getter
    @Setter
    @Builder
    public static class RecentForm {

        private Integer matches;

        private Integer runs;

        private Double averageRuns;

        private Double averageStrikeRate;

        private Integer fours;

        private Integer sixes;

        private Integer wickets;

        private Double formScore;
    }


    @Getter
    @Setter
    @Builder
    public static class MatchTrend {

        private Long matchId;

        private String matchDate;

        private String opponent;

        private String teamName;

        private Integer runs;

        private Integer ballsFaced;

        private Integer fours;

        private Integer sixes;

        private Double strikeRate;

        private Integer wickets;

        private Integer runsConceded;

        private Double bowlingEconomy;
    }
}