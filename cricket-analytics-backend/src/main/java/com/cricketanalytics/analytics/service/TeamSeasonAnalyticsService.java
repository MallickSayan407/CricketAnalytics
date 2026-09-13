package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.TeamSeasonStandingResponseDTO;

import java.util.List;

public interface TeamSeasonAnalyticsService {

    List<TeamSeasonStandingResponseDTO> getSeasonStandings(
            Long seasonId
    );
}