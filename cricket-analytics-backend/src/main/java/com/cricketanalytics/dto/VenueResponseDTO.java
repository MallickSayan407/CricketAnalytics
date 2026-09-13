package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class VenueResponseDTO {

    private Long id;
    private String name;
    private String city;
    private String country;
    private Integer capacity;
}