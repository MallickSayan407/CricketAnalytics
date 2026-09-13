package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class SeasonResponseDTO {

    private Long id;
    private String name;
    private Integer startYear;
    private Integer endYear;

    private Long competitionId;
    private String competitionName;
    private String competitionFormat;
}