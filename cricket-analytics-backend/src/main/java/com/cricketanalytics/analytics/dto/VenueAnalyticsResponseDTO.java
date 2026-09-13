package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class VenueAnalyticsResponseDTO {

    private Long venueId;

    private String venueName;

    private String city;

    private String country;

    private Integer capacity;

    private Integer totalMatches;

    private Integer completedMatches;

    private Integer team1Wins;

    private Integer team2Wins;

    private Integer tiedMatches;

    private Integer noResultMatches;

    private Double averageFirstInningsScore;

    private Double averageSecondInningsScore;

    private Double averageMatchRuns;

    private Integer highestTeamScore;

    private Integer lowestTeamScore;

    private Double averageRunRate;

    private Integer totalFours;

    private Integer totalSixes;
}