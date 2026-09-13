package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.SeasonAnalyticsResponseDTO;

public interface SeasonAnalyticsService {

    SeasonAnalyticsResponseDTO getSeasonAnalytics(Long seasonId);
}