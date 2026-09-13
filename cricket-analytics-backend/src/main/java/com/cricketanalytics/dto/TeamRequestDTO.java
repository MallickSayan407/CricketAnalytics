package com.cricketanalytics.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class TeamRequestDTO {

    @NotBlank(message = "Team name is required")
    private String name;

    @NotBlank(message = "Short name is required")
    @Size(min = 3, max = 3, message = "Short name must contain exactly 3 characters")
    private String shortName;

    @NotBlank(message = "Country is required")
    private String country;

    private String logoUrl;
}