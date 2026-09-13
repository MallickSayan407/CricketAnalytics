package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class CompetitionResponseDTO {

    private Long id;

    private String name;

    private String type;

    private String format;
}