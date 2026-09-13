package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.PlayerTrendResponseDTO;
import com.cricketanalytics.analytics.service.PlayerTrendService;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerMatchPerformance;
import com.cricketanalytics.entity.PlayerStatistics;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.PlayerMatchPerformanceRepository;
import com.cricketanalytics.repository.PlayerRepository;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.Comparator;
import java.util.List;

@Service
@RequiredArgsConstructor
public class PlayerTrendServiceImpl
        implements PlayerTrendService {

    private final PlayerRepository playerRepository;

    private final PlayerMatchPerformanceRepository
            performanceRepository;

    @Override
    public PlayerTrendResponseDTO getPlayerTrends(
            Long playerId,
            Long competitionId,
            Long seasonId) {

        Player player =
                playerRepository.findById(playerId)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Player not found with id: "
                                                + playerId
                                )
                        );

        if (seasonId != null && competitionId == null) {
            throw new IllegalArgumentException(
                    "competitionId is required when seasonId is provided"
            );
        }

        List<PlayerMatchPerformance> performances =
                performanceRepository
                        .findByPlayer_Id(playerId)
                        .stream()
                        .filter(performance ->
                                matchesFilters(
                                        performance,
                                        competitionId,
                                        seasonId
                                )
                        )
                        .sorted(
                                Comparator.comparing(
                                        performance ->
                                                performance
                                                        .getMatch()
                                                        .getMatchDate()
                                )
                        )
                        .toList();

        return PlayerTrendResponseDTO
                .builder()
                .playerId(player.getId())
                .playerName(player.getName())
                .recentForm(
                        calculateRecentForm(
                                performances
                        )
                )
                .matchTrend(
                        performances.stream()
                                .map(this::mapMatchTrend)
                                .toList()
                )
                .build();
    }

    private boolean matchesFilters(
            PlayerMatchPerformance performance,
            Long competitionId,
            Long seasonId) {

        Match match = performance.getMatch();

        if (match == null) {
            return false;
        }

        if (competitionId != null) {

            if (match.getCompetition() == null
                    || !competitionId.equals(
                            match.getCompetition().getId()
                    )) {

                return false;
            }
        }

        if (seasonId != null) {

            if (match.getSeason() == null
                    || !seasonId.equals(
                            match.getSeason().getId()
                    )) {

                return false;
            }
        }

        return true;
    }

    private PlayerTrendResponseDTO.RecentForm
    calculateRecentForm(
            List<PlayerMatchPerformance> performances) {

        if (performances.isEmpty()) {

            return PlayerTrendResponseDTO
                    .RecentForm
                    .builder()
                    .matches(0)
                    .runs(0)
                    .averageRuns(0.0)
                    .averageStrikeRate(0.0)
                    .fours(0)
                    .sixes(0)
                    .wickets(0)
                    .formScore(0.0)
                    .build();
        }

        /*
         * Recent form means the five most recent
         * matches after applying the requested filters.
         */

        List<PlayerMatchPerformance> recentMatches =
                performances.stream()
                        .sorted(
                                Comparator.comparing(
                                        performance ->
                                                performance
                                                        .getMatch()
                                                        .getMatchDate(),
                                        Comparator.reverseOrder()
                                )
                        )
                        .limit(5)
                        .toList();

        int matches =
                recentMatches.size();

        int runs =
                recentMatches.stream()
                        .mapToInt(performance ->
                                safeInt(
                                        performance.getBattingRuns()
                                )
                        )
                        .sum();

        int fours =
                recentMatches.stream()
                        .mapToInt(performance ->
                                safeInt(
                                        performance.getFours()
                                )
                        )
                        .sum();

        int sixes =
                recentMatches.stream()
                        .mapToInt(performance ->
                                safeInt(
                                        performance.getSixes()
                                )
                        )
                        .sum();

        int wickets =
                recentMatches.stream()
                        .mapToInt(performance ->
                                safeInt(
                                        performance.getWickets()
                                )
                        )
                        .sum();

        double averageRuns =
                matches > 0
                        ? runs / (double) matches
                        : 0.0;

        /*
         * Calculate recent strike rate from total runs
         * and total balls rather than averaging individual
         * strike rates.
         */
        int totalBallsFaced =
                recentMatches.stream()
                        .mapToInt(performance ->
                                safeInt(
                                        performance.getBallsFaced()
                                )
                        )
                        .sum();

        double averageStrikeRate =
                totalBallsFaced > 0
                        ? runs * 100.0 / totalBallsFaced
                        : 0.0;

        double formScore =
                calculateFormScore(
                        averageRuns,
                        averageStrikeRate,
                        wickets
                );

        return PlayerTrendResponseDTO
                .RecentForm
                .builder()
                .matches(matches)
                .runs(runs)
                .averageRuns(
                        round(averageRuns)
                )
                .averageStrikeRate(
                        round(averageStrikeRate)
                )
                .fours(fours)
                .sixes(sixes)
                .wickets(wickets)
                .formScore(
                        round(formScore)
                )
                .build();
    }

    private double calculateFormScore(
            double averageRuns,
            double strikeRate,
            int wickets) {

        /*
         * Prototype score.
         *
         * Batting:
         *  - average runs contributes up to 60
         *  - strike rate contributes up to 30
         *
         * Bowling:
         *  - wickets contribute up to 10
         *
         * This can later be replaced by the ML model.
         */

        double runComponent =
                Math.min(
                        averageRuns / 100.0 * 60.0,
                        60.0
                );

        double strikeRateComponent =
                Math.min(
                        strikeRate / 150.0 * 30.0,
                        30.0
                );

        double wicketComponent =
                Math.min(
                        wickets * 2.0,
                        10.0
                );

        return Math.min(
                runComponent
                        + strikeRateComponent
                        + wicketComponent,
                100.0
        );
    }

    private PlayerTrendResponseDTO.MatchTrend
    mapMatchTrend(
            PlayerMatchPerformance performance) {

        Match match =
                performance.getMatch();

        String opponent =
                findOpponent(
                        performance,
                        match
                );

        String teamName =
                performance.getTeam() != null
                        ? performance.getTeam().getName()
                        : (
                            performance.getPlayer() != null
                                    && performance.getPlayer().getTeam() != null
                                    ? performance.getPlayer()
                                            .getTeam()
                                            .getName()
                                    : null
                        );

        return PlayerTrendResponseDTO
                .MatchTrend
                .builder()
                .matchId(
                        match != null
                                ? match.getId()
                                : null
                )
                .matchDate(
                        match != null
                                && match.getMatchDate() != null
                                ? match.getMatchDate()
                                        .toString()
                                : null
                )
                .opponent(opponent)
                .teamName(teamName)
                .runs(
                        performance.getBattingRuns()
                )
                .ballsFaced(
                        performance.getBallsFaced()
                )
                .fours(
                        performance.getFours()
                )
                .sixes(
                        performance.getSixes()
                )
                .strikeRate(
                        performance.getBattingStrikeRate()
                )
                .wickets(
                        performance.getWickets()
                )
                .runsConceded(
                        performance.getRunsConceded()
                )
                .bowlingEconomy(
                        performance.getBowlingEconomy()
                )
                .build();
    }

    private String findOpponent(
            PlayerMatchPerformance performance,
            Match match) {

        if (performance == null
                || match == null) {

            return null;
        }

        Long playerTeamId = null;

        if (performance.getTeam() != null) {

            playerTeamId =
                    performance.getTeam().getId();

        } else if (performance.getPlayer() != null
                && performance.getPlayer().getTeam() != null) {

            playerTeamId =
                    performance.getPlayer()
                            .getTeam()
                            .getId();
        }

        if (playerTeamId == null) {
            return null;
        }

        if (match.getTeam1() != null
                && playerTeamId.equals(
                        match.getTeam1().getId()
                )) {

            return match.getTeam2() != null
                    ? match.getTeam2().getName()
                    : null;
        }

        if (match.getTeam2() != null
                && playerTeamId.equals(
                        match.getTeam2().getId()
                )) {

            return match.getTeam1() != null
                    ? match.getTeam1().getName()
                    : null;
        }

        return null;
    }

    private int safeInt(Integer value) {

        return value != null
                ? value
                : 0;
    }

    private double safeDouble(Double value) {

        return value != null
                ? value
                : 0.0;
    }

    private double round(double value) {

        return Math.round(value * 100.0)
                / 100.0;
    }
}