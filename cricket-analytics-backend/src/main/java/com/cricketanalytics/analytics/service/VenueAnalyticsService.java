package com.cricketanalytics.analytics.service;

import com.cricketanalytics.analytics.dto.VenueAnalyticsResponseDTO;

public interface VenueAnalyticsService {

    VenueAnalyticsResponseDTO getVenueAnalytics(Long venueId);
}