package com.cricketanalytics.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PlayerRequestDTO {

    @NotBlank(message = "Player name is required")
    private String name;

    @Size(max = 100, message = "External ID cannot exceed 100 characters")
    private String externalId;

    @NotBlank(message = "Player role is required")
    private String role;

    private String battingStyle;

    private String bowlingStyle;

    private String avatarUrl;

    private Long teamId;
}