package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.PlayerAnalyticsResponseDTO;
import com.cricketanalytics.analytics.dto.PlayerAnalyticsResponseDTO.CareerStats;
import com.cricketanalytics.analytics.dto.PlayerAnalyticsResponseDTO.MatchPerformanceSummary;
import com.cricketanalytics.analytics.service.PlayerAnalyticsService;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerMatchPerformance;
import com.cricketanalytics.entity.PlayerStatistics;
import com.cricketanalytics.repository.PlayerMatchPerformanceRepository;
import com.cricketanalytics.repository.PlayerRepository;
import com.cricketanalytics.repository.PlayerStatisticsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PlayerAnalyticsServiceImpl implements PlayerAnalyticsService {

    private final PlayerRepository playerRepository;
    private final PlayerStatisticsRepository statisticsRepository;
    private final PlayerMatchPerformanceRepository performanceRepository;


    @Override
    public PlayerAnalyticsResponseDTO getPlayerAnalytics(
            Long playerId,
            Long competitionId,
            Long seasonId
    ) {

        Player player = playerRepository.findById(playerId)
                .orElseThrow(() ->
                        new RuntimeException(
                                "Player not found with ID: " + playerId
                        )
                );

        /*
         * ============================================================
         * LOAD PLAYER STATISTICS
         * ============================================================
         */

        List<PlayerStatistics> allStatistics =
                statisticsRepository.findByPlayer_Id(playerId);

        List<PlayerStatistics> filteredStatistics =
                filterStatistics(
                        allStatistics,
                        competitionId,
                        seasonId
                );


        /*
         * ============================================================
         * LOAD MATCH PERFORMANCES
         * ============================================================
         */

        List<PlayerMatchPerformance> allPerformances =
                performanceRepository.findByPlayer_Id(playerId);

        List<PlayerMatchPerformance> filteredPerformances =
                filterPerformances(
                        allPerformances,
                        competitionId,
                        seasonId
                );


        /*
         * ============================================================
         * CALCULATE CAREER / FILTERED STATISTICS
         * ============================================================
         */

        CareerStats careerStats;

        if (!filteredPerformances.isEmpty()) {

            careerStats =
                    calculateCareerStatsFromPerformances(
                            filteredPerformances,
                            filteredStatistics
                    );

        } else {

            careerStats =
                    calculateCareerStatsFromStatistics(
                            filteredStatistics
                    );
        }


        /*
         * ============================================================
         * MATCH PERFORMANCE SUMMARY
         * ============================================================
         */

        MatchPerformanceSummary matchPerformance =
                calculateMatchPerformanceSummary(
                        filteredPerformances
                );


        /*
         * ============================================================
         * PLAYER TEAM
         * ============================================================
         *
         * This is the player's current/default team.
         *
         * Historical team participation is stored in
         * PlayerMatchPerformance.team.
         */

        String teamName = null;
        String teamShortName = null;

        if (player.getTeam() != null) {

            teamName = player.getTeam().getName();
            teamShortName = player.getTeam().getShortName();
        }


        /*
         * ============================================================
         * BUILD RESPONSE
         * ============================================================
         */

        return PlayerAnalyticsResponseDTO.builder()
                .playerId(player.getId())
                .playerName(player.getName())
                .teamName(teamName)
                .teamShortName(teamShortName)
                .careerStats(careerStats)
                .matchPerformance(matchPerformance)
                .build();
    }


    /*
     * ============================================================
     * FILTER PLAYER STATISTICS
     * ============================================================
     */

    private List<PlayerStatistics> filterStatistics(
            List<PlayerStatistics> statistics,
            Long competitionId,
            Long seasonId
    ) {

        if (statistics == null || statistics.isEmpty()) {
            return new ArrayList<>();
        }

        return statistics.stream()
                .filter(Objects::nonNull)
                .filter(stat -> {

                    /*
                     * Overall career
                     */
                    if (competitionId == null && seasonId == null) {
                        return true;
                    }


                    /*
                     * Competition filter
                     */
                    if (competitionId != null) {

                        if (stat.getCompetition() == null) {
                            return false;
                        }

                        if (!competitionId.equals(
                                stat.getCompetition().getId()
                        )) {
                            return false;
                        }
                    }


                    /*
                     * Season filter
                     */
                    if (seasonId != null) {

                        if (stat.getSeason() == null) {
                            return false;
                        }

                        if (!seasonId.equals(
                                stat.getSeason().getId()
                        )) {
                            return false;
                        }
                    }

                    return true;
                })
                .collect(Collectors.toList());
    }


    /*
     * ============================================================
     * FILTER MATCH PERFORMANCES
     * ============================================================
     */

    private List<PlayerMatchPerformance> filterPerformances(
            List<PlayerMatchPerformance> performances,
            Long competitionId,
            Long seasonId
    ) {

        if (performances == null || performances.isEmpty()) {
            return new ArrayList<>();
        }

        return performances.stream()
                .filter(Objects::nonNull)
                .filter(performance -> {

                    if (performance.getMatch() == null) {
                        return false;
                    }


                    /*
                     * Overall career
                     */
                    if (competitionId == null && seasonId == null) {
                        return true;
                    }


                    /*
                     * Competition filter
                     */
                    if (competitionId != null) {

                        if (performance.getMatch().getCompetition() == null) {
                            return false;
                        }

                        if (!competitionId.equals(
                                performance.getMatch()
                                        .getCompetition()
                                        .getId()
                        )) {
                            return false;
                        }
                    }


                    /*
                     * Season filter
                     */
                    if (seasonId != null) {

                        if (performance.getMatch().getSeason() == null) {
                            return false;
                        }

                        if (!seasonId.equals(
                                performance.getMatch()
                                        .getSeason()
                                        .getId()
                        )) {
                            return false;
                        }
                    }

                    return true;
                })
                .collect(Collectors.toList());
    }


    /*
     * ============================================================
     * CAREER STATS FROM MATCH PERFORMANCE
     * ============================================================
     */

    private CareerStats calculateCareerStatsFromPerformances(
            List<PlayerMatchPerformance> performances,
            List<PlayerStatistics> statistics
    ) {

        int matches = performances.size();

        int runs = performances.stream()
                .mapToInt(this::safeBattingRuns)
                .sum();

        int ballsFaced = performances.stream()
                .mapToInt(this::safeBallsFaced)
                .sum();

        int fours = performances.stream()
                .mapToInt(this::safeFours)
                .sum();

        int sixes = performances.stream()
                .mapToInt(this::safeSixes)
                .sum();

        /*
         * count() returns long, so explicitly cast to int.
         */
        int notOuts = (int) performances.stream()
                .filter(this::safeNotOut)
                .count();

        int highestScore = performances.stream()
                .mapToInt(this::safeBattingRuns)
                .max()
                .orElse(0);

        int wickets = performances.stream()
                .mapToInt(this::safeWickets)
                .sum();

        int runsConceded = performances.stream()
                .mapToInt(this::safeRunsConceded)
                .sum();

        int ballsBowled = performances.stream()
                .mapToInt(this::safeBallsBowled)
                .sum();


        /*
         * Batting average
         *
         * Runs / dismissed innings
         */

        int dismissedInnings = (int) performances.stream()
                .filter(p -> safeBallsFaced(p) > 0)
                .filter(p -> !safeNotOut(p))
                .count();

        double battingAverage =
                dismissedInnings > 0
                        ? (double) runs / dismissedInnings
                        : 0.0;


        /*
         * Strike rate
         */

        double strikeRate =
                ballsFaced > 0
                        ? (double) runs * 100.0 / ballsFaced
                        : 0.0;


        /*
         * Bowling economy
         */

        double economy =
                ballsBowled > 0
                        ? (double) runsConceded * 6.0 / ballsBowled
                        : 0.0;


        /*
         * Bowling average
         */

        double bowlingAverage =
                wickets > 0
                        ? (double) runsConceded / wickets
                        : 0.0;


        int fifties =
                calculateFifties(statistics);

        int centuries =
                calculateCenturies(statistics);

        int fiveWicketHauls =
                calculateFiveWicketHauls(statistics);


        return CareerStats.builder()
                .matches(matches)
                .runs(runs)
                .highestScore(highestScore)
                .fifties(fifties)
                .centuries(centuries)
                .notOuts(notOuts)
                .battingAverage(round(battingAverage))
                .strikeRate(round(strikeRate))
                .wickets(wickets)
                .runsConceded(runsConceded)
                .economy(round(economy))
                .bowlingAverage(round(bowlingAverage))
                .fiveWicketHauls(fiveWicketHauls)
                .build();
    }


    /*
     * ============================================================
     * FALLBACK: PLAYER STATISTICS
     * ============================================================
     */

    private CareerStats calculateCareerStatsFromStatistics(
            List<PlayerStatistics> statistics
    ) {

        if (statistics == null || statistics.isEmpty()) {

            return emptyCareerStats();
        }


        List<PlayerStatistics> rows =
                chooseBestStatisticsRows(statistics);


        int matches = rows.stream()
                .mapToInt(this::safeMatches)
                .sum();

        int runs = rows.stream()
                .mapToInt(this::safeRuns)
                .sum();

        int highestScore = rows.stream()
                .mapToInt(this::safeHighestScore)
                .max()
                .orElse(0);

        int notOuts = rows.stream()
                .mapToInt(this::safeNotOuts)
                .sum();

        int fifties = rows.stream()
                .mapToInt(this::safeFifties)
                .sum();

        int centuries = rows.stream()
                .mapToInt(this::safeCenturies)
                .sum();

        int wickets = rows.stream()
                .mapToInt(this::safeWicketsStats)
                .sum();

        int runsConceded = rows.stream()
                .mapToInt(this::safeRunsConcededStats)
                .sum();

        int ballsFaced = rows.stream()
                .mapToInt(this::safeBallsFacedStats)
                .sum();

        int ballsBowled = rows.stream()
                .mapToInt(this::safeBallsBowledStats)
                .sum();


        int dismissedInnings = rows.stream()
                .mapToInt(stat ->
                        Math.max(
                                0,
                                safeBattingInnings(stat)
                                        - safeNotOuts(stat)
                        )
                )
                .sum();


        double battingAverage =
                dismissedInnings > 0
                        ? (double) runs / dismissedInnings
                        : 0.0;

        double strikeRate =
                ballsFaced > 0
                        ? (double) runs * 100.0 / ballsFaced
                        : 0.0;

        double economy =
                ballsBowled > 0
                        ? (double) runsConceded * 6.0 / ballsBowled
                        : 0.0;

        double bowlingAverage =
                wickets > 0
                        ? (double) runsConceded / wickets
                        : 0.0;

        int fiveWicketHauls = rows.stream()
                .mapToInt(this::safeFiveWicketHauls)
                .sum();


        return CareerStats.builder()
                .matches(matches)
                .runs(runs)
                .highestScore(highestScore)
                .fifties(fifties)
                .centuries(centuries)
                .notOuts(notOuts)
                .battingAverage(round(battingAverage))
                .strikeRate(round(strikeRate))
                .wickets(wickets)
                .runsConceded(runsConceded)
                .economy(round(economy))
                .bowlingAverage(round(bowlingAverage))
                .fiveWicketHauls(fiveWicketHauls)
                .build();
    }


    /*
     * ============================================================
     * CHOOSE STATISTICS ROWS
     * ============================================================
     *
     * Never add CAREER rows and SEASON rows together.
     */

    private List<PlayerStatistics> chooseBestStatisticsRows(
            List<PlayerStatistics> statistics
    ) {

        if (statistics == null || statistics.isEmpty()) {
            return new ArrayList<>();
        }


        List<PlayerStatistics> careerRows =
                statistics.stream()
                        .filter(stat ->
                                stat.getScope() != null &&
                                "CAREER".equalsIgnoreCase(
                                        stat.getScope()
                                )
                        )
                        .collect(Collectors.toList());


        if (!careerRows.isEmpty()) {
            return careerRows;
        }


        return statistics.stream()
                .filter(stat ->
                        stat.getScope() == null ||
                                "SEASON".equalsIgnoreCase(
                                        stat.getScope()
                                )
                )
                .collect(Collectors.toList());
    }


    /*
     * ============================================================
     * MATCH PERFORMANCE SUMMARY
     * ============================================================
     */

    private MatchPerformanceSummary calculateMatchPerformanceSummary(
            List<PlayerMatchPerformance> performances
    ) {

        if (performances == null || performances.isEmpty()) {

            return MatchPerformanceSummary.builder()
                    .matches(0)
                    .runs(0)
                    .ballsFaced(0)
                    .fours(0)
                    .sixes(0)
                    .averageStrikeRate(0.0)
                    .wickets(0)
                    .runsConceded(0)
                    .averageEconomy(0.0)
                    .build();
        }


        int matches = performances.size();

        int runs = performances.stream()
                .mapToInt(this::safeBattingRuns)
                .sum();

        int ballsFaced = performances.stream()
                .mapToInt(this::safeBallsFaced)
                .sum();

        int fours = performances.stream()
                .mapToInt(this::safeFours)
                .sum();

        int sixes = performances.stream()
                .mapToInt(this::safeSixes)
                .sum();

        int wickets = performances.stream()
                .mapToInt(this::safeWickets)
                .sum();

        int runsConceded = performances.stream()
                .mapToInt(this::safeRunsConceded)
                .sum();

        int ballsBowled = performances.stream()
                .mapToInt(this::safeBallsBowled)
                .sum();


        double averageStrikeRate =
                ballsFaced > 0
                        ? (double) runs * 100.0 / ballsFaced
                        : 0.0;

        double averageEconomy =
                ballsBowled > 0
                        ? (double) runsConceded * 6.0 / ballsBowled
                        : 0.0;


        return MatchPerformanceSummary.builder()
                .matches(matches)
                .runs(runs)
                .ballsFaced(ballsFaced)
                .fours(fours)
                .sixes(sixes)
                .averageStrikeRate(round(averageStrikeRate))
                .wickets(wickets)
                .runsConceded(runsConceded)
                .averageEconomy(round(averageEconomy))
                .build();
    }


    /*
     * ============================================================
     * FIFTIES / CENTURIES / FIVE-WICKET HAULS
     * ============================================================
     */

    private int calculateFifties(
            List<PlayerStatistics> statistics
    ) {

        return chooseBestStatisticsRows(statistics)
                .stream()
                .mapToInt(this::safeFifties)
                .sum();
    }


    private int calculateCenturies(
            List<PlayerStatistics> statistics
    ) {

        return chooseBestStatisticsRows(statistics)
                .stream()
                .mapToInt(this::safeCenturies)
                .sum();
    }


    private int calculateFiveWicketHauls(
            List<PlayerStatistics> statistics
    ) {

        return chooseBestStatisticsRows(statistics)
                .stream()
                .mapToInt(this::safeFiveWicketHauls)
                .sum();
    }


    /*
     * ============================================================
     * PLAYER MATCH PERFORMANCE HELPERS
     * ============================================================
     */

    private int safeBattingRuns(PlayerMatchPerformance p) {
        return p.getBattingRuns() == null
                ? 0
                : p.getBattingRuns();
    }


    private int safeBallsFaced(PlayerMatchPerformance p) {
        return p.getBallsFaced() == null
                ? 0
                : p.getBallsFaced();
    }


    private int safeFours(PlayerMatchPerformance p) {
        return p.getFours() == null
                ? 0
                : p.getFours();
    }


    private int safeSixes(PlayerMatchPerformance p) {
        return p.getSixes() == null
                ? 0
                : p.getSixes();
    }


    private boolean safeNotOut(PlayerMatchPerformance p) {
        return Boolean.TRUE.equals(p.getNotOut());
    }


    private int safeBallsBowled(PlayerMatchPerformance p) {
        return p.getBallsBowled() == null
                ? 0
                : p.getBallsBowled();
    }


    private int safeRunsConceded(PlayerMatchPerformance p) {
        return p.getRunsConceded() == null
                ? 0
                : p.getRunsConceded();
    }


    private int safeWickets(PlayerMatchPerformance p) {
        return p.getWickets() == null
                ? 0
                : p.getWickets();
    }


    /*
     * ============================================================
     * PLAYER STATISTICS HELPERS
     * ============================================================
     */

    private int safeMatches(PlayerStatistics s) {
        return s.getMatches() == null
                ? 0
                : s.getMatches();
    }


    private int safeRuns(PlayerStatistics s) {
        return s.getRuns() == null
                ? 0
                : s.getRuns();
    }


    private int safeHighestScore(PlayerStatistics s) {
        return s.getHighestScore() == null
                ? 0
                : s.getHighestScore();
    }


    private int safeNotOuts(PlayerStatistics s) {
        return s.getNotOuts() == null
                ? 0
                : s.getNotOuts();
    }


    private int safeFifties(PlayerStatistics s) {
        return s.getFifties() == null
                ? 0
                : s.getFifties();
    }


    private int safeCenturies(PlayerStatistics s) {
        return s.getCenturies() == null
                ? 0
                : s.getCenturies();
    }


    private int safeWicketsStats(PlayerStatistics s) {
        return s.getWickets() == null
                ? 0
                : s.getWickets();
    }


    private int safeRunsConcededStats(PlayerStatistics s) {
        return s.getRunsConceded() == null
                ? 0
                : s.getRunsConceded();
    }


    private int safeBallsFacedStats(PlayerStatistics s) {
        return s.getBallsFaced() == null
                ? 0
                : s.getBallsFaced();
    }


    private int safeBallsBowledStats(PlayerStatistics s) {
        return s.getBallsBowled() == null
                ? 0
                : s.getBallsBowled();
    }


    private int safeBattingInnings(PlayerStatistics s) {
        return s.getBattingInnings() == null
                ? 0
                : s.getBattingInnings();
    }


    private int safeFiveWicketHauls(PlayerStatistics s) {
        return s.getFiveWicketHauls() == null
                ? 0
                : s.getFiveWicketHauls();
    }


    /*
     * ============================================================
     * EMPTY RESPONSE
     * ============================================================
     */

    private CareerStats emptyCareerStats() {

        return CareerStats.builder()
                .matches(0)
                .runs(0)
                .highestScore(0)
                .fifties(0)
                .centuries(0)
                .notOuts(0)
                .battingAverage(0.0)
                .strikeRate(0.0)
                .wickets(0)
                .runsConceded(0)
                .economy(0.0)
                .bowlingAverage(0.0)
                .fiveWicketHauls(0)
                .build();
    }


    /*
     * ============================================================
     * ROUNDING
     * ============================================================
     */

    private double round(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}