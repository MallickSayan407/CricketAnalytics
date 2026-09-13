package com.cricketanalytics.simulator.dto;

public record ODIPlayoffResult(
        String semiFinal1TeamA,
        String semiFinal1TeamB,
        String semiFinal1Winner,

        String semiFinal2TeamA,
        String semiFinal2TeamB,
        String semiFinal2Winner,

        String finalTeamA,
        String finalTeamB,
        String champion
) {
}