package com.cricketanalytics.simulator.dto;

import java.util.List;

public record ODIMonteCarloResult(
        int simulations,
        List<ODIMonteCarloTeamResult> results
) {
}