package com.cricketanalytics.service;

import com.cricketanalytics.dto.VenueRequestDTO;
import com.cricketanalytics.dto.VenueResponseDTO;

import java.util.List;

public interface VenueService {

    VenueResponseDTO createVenue(VenueRequestDTO request);

    List<VenueResponseDTO> getAllVenues();

    VenueResponseDTO getVenueById(Long id);

    List<VenueResponseDTO> getVenuesByCountry(String country);

    List<VenueResponseDTO> getVenuesByCity(String city);

    VenueResponseDTO updateVenue(
            Long id,
            VenueRequestDTO request
    );

    void deleteVenue(Long id);
}