package com.cricketanalytics.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class SeasonRequestDTO {

    @NotBlank(message = "Season name is required")
    private String name;

    @NotNull(message = "Start year is required")
    @Min(value = 1900, message = "Start year must be 1900 or later")
    @Max(value = 2100, message = "Start year must not exceed 2100")
    private Integer startYear;

    @Min(value = 1900, message = "End year must be 1900 or later")
    @Max(value = 2100, message = "End year must not exceed 2100")
    private Integer endYear;

    @NotNull(message = "Competition ID is required")
    private Long competitionId;
}