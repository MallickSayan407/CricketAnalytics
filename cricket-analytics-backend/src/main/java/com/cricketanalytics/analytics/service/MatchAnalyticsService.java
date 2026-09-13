package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.MatchAnalyticsResponseDTO;

public interface MatchAnalyticsService {

    MatchAnalyticsResponseDTO getMatchAnalytics(Long matchId);
}