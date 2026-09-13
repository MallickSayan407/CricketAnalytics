package com.cricketanalytics.dto;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class PlayerResponseDTO {

    private Long id;

    private String name;

    private String externalId;

    private String role;

    private String battingStyle;

    private String bowlingStyle;

    private String avatarUrl;

    private Long teamId;

    private String teamName;

    private String teamShortName;
}