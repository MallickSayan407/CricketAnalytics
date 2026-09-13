package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.TeamAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.TeamAnalyticsService;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.TeamRepository;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TeamAnalyticsServiceImpl implements TeamAnalyticsService {

    private final TeamRepository teamRepository;

    private final MatchRepository matchRepository;

    private final MatchTeamStatsRepository statsRepository;


    @Override
    public TeamAnalyticsResponseDTO getTeamAnalytics(
            Long teamId,
            Long competitionId,
            Long seasonId) {

        /*
         * ---------------------------------------------------------
         * LOAD TEAM
         * ---------------------------------------------------------
         */

        Team team = teamRepository.findById(teamId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: " + teamId
                        )
                );


        /*
         * ---------------------------------------------------------
         * RETRIEVE ALL MATCHES INVOLVING THIS TEAM
         * ---------------------------------------------------------
         */

        List<Match> matches =
                matchRepository.findByTeam1_IdOrTeam2_Id(
                        teamId,
                        teamId
                );


        /*
         * ---------------------------------------------------------
         * APPLY COMPETITION / SEASON FILTERS
         * ---------------------------------------------------------
         */

        matches = filterMatches(
                matches,
                competitionId,
                seasonId
        );


        /*
         * ---------------------------------------------------------
         * RETRIEVE TEAM PERFORMANCE STATISTICS
         * ---------------------------------------------------------
         */

        List<MatchTeamStats> statistics =
                statsRepository.findByTeam_Id(teamId);


        /*
         * Apply the same competition/season
         * filters through the match relationship.
         */

        statistics = filterStatistics(
                statistics,
                competitionId,
                seasonId
        );


        /*
         * ---------------------------------------------------------
         * BUILD RESPONSE
         * ---------------------------------------------------------
         */

        return TeamAnalyticsResponseDTO.builder()

                .teamId(team.getId())

                .teamName(team.getName())

                .teamShortName(team.getShortName())

                .matchStats(
                        calculateMatchStats(
                                teamId,
                                matches
                        )
                )

                .performance(
                        calculatePerformance(
                                teamId,
                                statistics
                        )
                )

                .build();
    }


    /*
     * =========================================================
     * MATCH FILTERING
     * =========================================================
     */

    private List<Match> filterMatches(
            List<Match> matches,
            Long competitionId,
            Long seasonId) {

        return matches.stream()

                .filter(match -> {

                    /*
                     * Competition filter
                     */

                    if (competitionId != null) {

                        if (match.getCompetition() == null
                                || !Objects.equals(
                                match.getCompetition().getId(),
                                competitionId)) {

                            return false;
                        }
                    }


                    /*
                     * Season filter
                     */

                    if (seasonId != null) {

                        if (match.getSeason() == null
                                || !Objects.equals(
                                match.getSeason().getId(),
                                seasonId)) {

                            return false;
                        }
                    }


                    return true;
                })

                .collect(Collectors.toList());
    }


    /*
     * =========================================================
     * TEAM STATISTICS FILTERING
     * =========================================================
     */

    private List<MatchTeamStats> filterStatistics(
            List<MatchTeamStats> statistics,
            Long competitionId,
            Long seasonId) {

        return statistics.stream()

                .filter(stat -> {

                    Match match = stat.getMatch();

                    if (match == null) {
                        return false;
                    }


                    /*
                     * Competition filter
                     */

                    if (competitionId != null) {

                        if (match.getCompetition() == null
                                || !Objects.equals(
                                match.getCompetition().getId(),
                                competitionId)) {

                            return false;
                        }
                    }


                    /*
                     * Season filter
                     */

                    if (seasonId != null) {

                        if (match.getSeason() == null
                                || !Objects.equals(
                                match.getSeason().getId(),
                                seasonId)) {

                            return false;
                        }
                    }


                    return true;
                })

                .collect(Collectors.toList());
    }


    /*
     * =========================================================
     * MATCH RESULTS
     * =========================================================
     */

    private TeamAnalyticsResponseDTO.MatchStats
    calculateMatchStats(
            Long teamId,
            List<Match> matches) {

        int matchesPlayed = 0;

        int wins = 0;

        int losses = 0;

        int ties = 0;

        int noResults = 0;


        for (Match match : matches) {

            String status = match.getMatchStatus();

            /*
             * ---------------------------------------------------------
             * NO RESULT
             * ---------------------------------------------------------
             *
             * A no-result match counts as a match played,
             * but it is neither a win nor a loss.
             */

            if (status != null
                    && status.equalsIgnoreCase("NO_RESULT")) {

                matchesPlayed++;

                noResults++;

                continue;
            }


            /*
             * ---------------------------------------------------------
             * COMPLETED MATCH
             * ---------------------------------------------------------
             */

            if (status == null
                    || !status.equalsIgnoreCase("COMPLETED")) {

                /*
                 * Ignore unknown / unsupported match statuses.
                 */

                continue;
            }


            matchesPlayed++;


            /*
             * ---------------------------------------------------------
             * COMPLETED MATCH WITHOUT A WINNER
             * ---------------------------------------------------------
             *
             * This can represent a tie or another result where
             * no winner is stored.
             */

            if (match.getWinner() == null) {

                String result =
                        match.getResultDescription();


                if (result != null
                        && result
                        .toLowerCase()
                        .contains("tie")) {

                    ties++;

                } else {

                    noResults++;
                }

                continue;
            }


            /*
             * ---------------------------------------------------------
             * DETERMINE WINNER
             * ---------------------------------------------------------
             */

            Long winnerId =
                    match.getWinner().getId();


            if (Objects.equals(
                    winnerId,
                    teamId)) {

                wins++;

            } else {

                losses++;
            }
        }


        /*
         * ---------------------------------------------------------
         * WIN PERCENTAGE
         * ---------------------------------------------------------
         *
         * Win percentage is calculated against all matches played,
         * including no-results and ties.
         */

        double winPercentage = 0.0;


        if (matchesPlayed > 0) {

            winPercentage =
                    wins * 100.0
                            / matchesPlayed;
        }


        return TeamAnalyticsResponseDTO
                .MatchStats
                .builder()

                .matches(matchesPlayed)

                .wins(wins)

                .losses(losses)

                .ties(ties)

                .noResults(noResults)

                .winPercentage(
                        round(winPercentage)
                )

                .build();
    }


    /*
     * =========================================================
     * TEAM PERFORMANCE
     * =========================================================
     *
     * Calculates:
     *
     * Runs Scored
     * Average Runs
     * Wickets Lost
     * Run Rate
     * Fours
     * Sixes
     *
     * PLUS:
     *
     * Runs Conceded
     * Balls Bowled
     * Bowling Rate
     * Net Run Rate
     *
     * The team's own MatchTeamStats contains its batting
     * performance.
     *
     * The opponent's MatchTeamStats contains the runs
     * conceded by this team.
     *
     * This follows the same approach used by the season
     * standings service.
     */

    private TeamAnalyticsResponseDTO.Performance
    calculatePerformance(
            Long teamId,
            List<MatchTeamStats> statistics) {

        if (statistics.isEmpty()) {

            return TeamAnalyticsResponseDTO
                    .Performance
                    .builder()

                    .runsScored(0)

                    .averageRuns(0.0)

                    .wicketsLost(0)

                    .averageRunRate(0.0)

                    .runsConceded(0)

                    .bowlingRate(0.0)

                    .netRunRate(0.0)

                    .fours(0)

                    .sixes(0)

                    .build();
        }


        /*
         * ---------------------------------------------------------
         * TEAM BATTING TOTALS
         * ---------------------------------------------------------
         */

        int runsScored =
                statistics.stream()

                        .mapToInt(stat ->
                                safeInt(
                                        stat.getRuns()
                                )
                        )

                        .sum();


        int wicketsLost =
                statistics.stream()

                        .mapToInt(stat ->
                                safeInt(
                                        stat.getWickets()
                                )
                        )

                        .sum();


        int fours =
                statistics.stream()

                        .mapToInt(stat ->
                                safeInt(
                                        stat.getFours()
                                )
                        )

                        .sum();


        int sixes =
                statistics.stream()

                        .mapToInt(stat ->
                                safeInt(
                                        stat.getSixes()
                                )
                        )

                        .sum();


        int totalBalls =
                statistics.stream()

                        .mapToInt(stat ->
                                safeInt(
                                        stat.getTotalBalls()
                                )
                        )

                        .sum();


        /*
         * ---------------------------------------------------------
         * OPPONENT / BOWLING TOTALS
         * ---------------------------------------------------------
         *
         * For every match, find the opponent's MatchTeamStats.
         *
         * Opponent runs = runs conceded.
         *
         * Opponent balls = balls bowled by our team.
         */

        int runsConceded = 0;

        int ballsBowled = 0;


        for (MatchTeamStats ownStats : statistics) {

            if (ownStats.getMatch() == null) {
                continue;
            }


            Long matchId =
                    ownStats.getMatch().getId();


            List<MatchTeamStats> allMatchStats =
                    statsRepository.findByMatch_Id(matchId);


            for (MatchTeamStats opponentStats :
                    allMatchStats) {

                if (opponentStats.getTeam() == null) {
                    continue;
                }


                Long opponentTeamId =
                        opponentStats.getTeam().getId();


                /*
                 * Ignore our own team.
                 */

                if (Objects.equals(
                        opponentTeamId,
                        teamId)) {

                    continue;
                }


                /*
                 * Opponent runs are our runs conceded.
                 */

                runsConceded += safeInt(
                        opponentStats.getRuns()
                );


                /*
                 * Opponent innings balls are our
                 * bowling balls.
                 */

                ballsBowled += safeInt(
                        opponentStats.getTotalBalls()
                );
            }
        }


        /*
         * ---------------------------------------------------------
         * AVERAGE RUNS
         * ---------------------------------------------------------
         */

        double averageRuns =
                runsScored
                        / (double) statistics.size();


        /*
         * ---------------------------------------------------------
         * RUN RATE
         * ---------------------------------------------------------
         *
         * Run Rate = Runs / Overs
         *
         * Overs = balls / 6
         *
         * Therefore:
         *
         * Run Rate = Runs * 6 / Balls
         */

        double averageRunRate = 0.0;


        if (totalBalls > 0) {

            averageRunRate =
                    runsScored * 6.0
                            / totalBalls;
        }


        /*
         * ---------------------------------------------------------
         * BOWLING RATE
         * ---------------------------------------------------------
         *
         * Bowling Rate = Runs Conceded / Overs Bowled
         *
         * Therefore:
         *
         * Bowling Rate =
         * Runs Conceded * 6 / Balls Bowled
         */

        double bowlingRate = 0.0;


        if (ballsBowled > 0) {

            bowlingRate =
                    runsConceded * 6.0
                            / ballsBowled;
        }


        /*
         * ---------------------------------------------------------
         * NET RUN RATE
         * ---------------------------------------------------------
         *
         * NRR =
         *
         * Run Rate - Bowling Rate
         */

        double netRunRate =
                averageRunRate
                        - bowlingRate;


        /*
         * ---------------------------------------------------------
         * BUILD PERFORMANCE RESPONSE
         * ---------------------------------------------------------
         */

        return TeamAnalyticsResponseDTO
                .Performance
                .builder()

                .runsScored(runsScored)

                .averageRuns(
                        round(averageRuns)
                )

                .wicketsLost(wicketsLost)

                .averageRunRate(
                        round(averageRunRate)
                )

                .runsConceded(
                        runsConceded
                )

                .bowlingRate(
                        round(bowlingRate)
                )

                .netRunRate(
                        round(netRunRate)
                )

                .fours(fours)

                .sixes(sixes)

                .build();
    }


    /*
     * =========================================================
     * HELPERS
     * =========================================================
     */

    private int safeInt(Integer value) {

        return value != null
                ? value
                : 0;
    }


    private double round(double value) {

        return Math.round(value * 100.0)
                / 100.0;
    }
}