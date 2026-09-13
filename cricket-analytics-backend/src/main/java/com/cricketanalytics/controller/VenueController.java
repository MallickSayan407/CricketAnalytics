package com.cricketanalytics.controller;

import com.cricketanalytics.dto.VenueRequestDTO;
import com.cricketanalytics.dto.VenueResponseDTO;
import com.cricketanalytics.service.VenueService;

import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/venues")
@RequiredArgsConstructor
public class VenueController {

    private final VenueService venueService;

    @PostMapping
    public ResponseEntity<VenueResponseDTO> createVenue(
            @Valid @RequestBody VenueRequestDTO request) {

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(venueService.createVenue(request));
    }

    @GetMapping
    public ResponseEntity<List<VenueResponseDTO>> getAllVenues() {

        return ResponseEntity.ok(
                venueService.getAllVenues()
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<VenueResponseDTO> getVenueById(
            @PathVariable("id") Long id) {

        return ResponseEntity.ok(
                venueService.getVenueById(id)
        );
    }

    @GetMapping("/country/{country}")
    public ResponseEntity<List<VenueResponseDTO>>
    getVenuesByCountry(
            @PathVariable("country") String country) {

        return ResponseEntity.ok(
                venueService.getVenuesByCountry(country)
        );
    }

    @GetMapping("/city/{city}")
    public ResponseEntity<List<VenueResponseDTO>>
    getVenuesByCity(
            @PathVariable("city") String city) {

        return ResponseEntity.ok(
                venueService.getVenuesByCity(city)
        );
    }

    @PutMapping("/{id}")
    public ResponseEntity<VenueResponseDTO> updateVenue(
            @PathVariable("id") Long id,
            @Valid @RequestBody VenueRequestDTO request) {

        return ResponseEntity.ok(
                venueService.updateVenue(id, request)
        );
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteVenue(
            @PathVariable("id") Long id) {

        venueService.deleteVenue(id);

        return ResponseEntity.noContent().build();
    }
}