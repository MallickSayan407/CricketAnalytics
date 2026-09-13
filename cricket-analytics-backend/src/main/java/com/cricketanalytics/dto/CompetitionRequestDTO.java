package com.cricketanalytics.dto;

import jakarta.validation.constraints.NotBlank;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class CompetitionRequestDTO {

    @NotBlank(message = "Competition name is required")
    private String name;

    @NotBlank(message = "Competition type is required")
    private String type;

    @NotBlank(message = "Competition format is required")
    private String format;
}