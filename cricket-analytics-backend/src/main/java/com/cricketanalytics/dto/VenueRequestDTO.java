package com.cricketanalytics.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class VenueRequestDTO {

    @NotBlank(message = "Venue name is required")
    private String name;

    @NotBlank(message = "City is required")
    private String city;

    @NotBlank(message = "Country is required")
    private String country;

    @Min(value = 1, message = "Capacity must be at least 1")
    @Max(value = 200000, message = "Capacity cannot exceed 200000")
    private Integer capacity;
}