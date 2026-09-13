package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Builder
public class MatchAnalyticsResponseDTO {

    private Long matchId;

    private String matchDate;

    private String matchStatus;

    private String stage;

    private String competitionName;

    private String competitionFormat;

    private String seasonName;

    private String venueName;

    private String venueCity;

    private String venueCountry;

    private TeamMatchSummary team1;

    private TeamMatchSummary team2;

    private String tossWinner;

    private String tossDecision;

    private String winner;

    private String resultDescription;

    private List<PlayerMatchSummary> playerPerformances;


    // =========================================================
    // TEAM MATCH SUMMARY
    // =========================================================

    @Getter
    @Setter
    @Builder
    public static class TeamMatchSummary {

        private Long teamId;

        private String teamName;

        private String teamShortName;

        private Integer runs;

        private Integer wickets;

        private Integer totalBalls;

        private String overs;

        private Integer fours;

        private Integer sixes;

        private Integer extras;

        private Double runRate;
    }


    // =========================================================
    // PLAYER MATCH SUMMARY
    // =========================================================

    @Getter
    @Setter
    @Builder
    public static class PlayerMatchSummary {

        private Long playerId;

        private String playerName;

        private String role;

        private String teamName;


        // -----------------------------------------------------
        // Batting
        // -----------------------------------------------------

        private Integer battingRuns;

        private Integer ballsFaced;

        private Integer fours;

        private Integer sixes;

        private Double battingStrikeRate;

        private Boolean notOut;


        // -----------------------------------------------------
        // Bowling
        // -----------------------------------------------------

        private Integer ballsBowled;

        /*
         * Display representation.
         *
         * Example:
         *
         * 61 balls → 10.1 overs
         */
        private String oversBowled;

        private Integer runsConceded;

        private Integer wickets;

        private Double bowlingEconomy;

        private Integer maidens;
    }
}