package com.cricketanalytics.service;

import com.cricketanalytics.dto.VenueRequestDTO;
import com.cricketanalytics.dto.VenueResponseDTO;
import com.cricketanalytics.entity.Venue;
import com.cricketanalytics.exception.DuplicateResourceException;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.VenueRepository;
import com.cricketanalytics.service.VenueService;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class VenueServiceImpl implements VenueService {

    private final VenueRepository venueRepository;

    @Override
    public VenueResponseDTO createVenue(VenueRequestDTO request) {

        if (venueRepository.existsByNameIgnoreCase(request.getName())) {
            throw new DuplicateResourceException(
                    "Venue already exists: " + request.getName()
            );
        }

        Venue venue = Venue.builder()
                .name(request.getName())
                .city(request.getCity())
                .country(request.getCountry())
                .capacity(request.getCapacity())
                .build();

        Venue savedVenue = venueRepository.save(venue);

        return mapToResponse(savedVenue);
    }

    @Override
    public List<VenueResponseDTO> getAllVenues() {

        return venueRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public VenueResponseDTO getVenueById(Long id) {

        Venue venue = venueRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Venue not found with id: " + id
                        )
                );

        return mapToResponse(venue);
    }

    @Override
    public List<VenueResponseDTO> getVenuesByCountry(
            String country) {

        return venueRepository
                .findByCountryIgnoreCase(country)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<VenueResponseDTO> getVenuesByCity(
            String city) {

        return venueRepository
                .findByCityIgnoreCase(city)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public VenueResponseDTO updateVenue(
            Long id,
            VenueRequestDTO request) {

        Venue venue = venueRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Venue not found with id: " + id
                        )
                );

        venueRepository.findByNameIgnoreCase(request.getName())
                .ifPresent(existingVenue -> {

                    if (!existingVenue.getId().equals(id)) {

                        throw new DuplicateResourceException(
                                "Venue already exists: "
                                        + request.getName()
                        );
                    }
                });

        venue.setName(request.getName());
        venue.setCity(request.getCity());
        venue.setCountry(request.getCountry());
        venue.setCapacity(request.getCapacity());

        Venue updatedVenue = venueRepository.save(venue);

        return mapToResponse(updatedVenue);
    }

    @Override
    public void deleteVenue(Long id) {

        if (!venueRepository.existsById(id)) {

            throw new ResourceNotFoundException(
                    "Venue not found with id: " + id
            );
        }

        venueRepository.deleteById(id);
    }

    private VenueResponseDTO mapToResponse(Venue venue) {

        return VenueResponseDTO.builder()
                .id(venue.getId())
                .name(venue.getName())
                .city(venue.getCity())
                .country(venue.getCountry())
                .capacity(venue.getCapacity())
                .build();
    }
}