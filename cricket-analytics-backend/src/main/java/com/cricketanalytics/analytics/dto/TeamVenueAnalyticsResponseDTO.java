package com.cricketanalytics.analytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class TeamVenueAnalyticsResponseDTO {

    private Long venueId;

    private String venueName;

    private Long teamId;

    private String teamName;

    private String teamShortName;

    private Integer matches;

    private Integer wins;

    private Integer losses;

    private Integer ties;

    private Integer noResults;

    private Double winPercentage;

    private Double averageRuns;

    private Double averageRunRate;
}