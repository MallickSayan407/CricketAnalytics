package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class TeamResponseDTO {

    private Long id;

    private String name;

    private String shortName;

    private String country;

    private String logoUrl;
}