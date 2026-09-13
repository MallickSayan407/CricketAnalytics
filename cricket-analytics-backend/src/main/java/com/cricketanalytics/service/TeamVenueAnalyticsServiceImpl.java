package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.TeamVenueAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.TeamVenueAnalyticsService;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.entity.Venue;
import com.cricketanalytics.exception.BadRequestException;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.TeamRepository;
import com.cricketanalytics.repository.VenueRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class TeamVenueAnalyticsServiceImpl
        implements TeamVenueAnalyticsService {

    private final VenueRepository venueRepository;

    private final TeamRepository teamRepository;

    private final MatchRepository matchRepository;

    private final MatchTeamStatsRepository matchTeamStatsRepository;

    @Override
    public TeamVenueAnalyticsResponseDTO getTeamVenueAnalytics(
            Long venueId,
            Long teamId
    ) {

        /*
         * ----------------------------------------
         * VALIDATE VENUE
         * ----------------------------------------
         */

        Venue venue = venueRepository.findById(venueId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Venue not found with id: " + venueId
                        )
                );

        /*
         * ----------------------------------------
         * VALIDATE TEAM
         * ----------------------------------------
         */

        Team team = teamRepository.findById(teamId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: " + teamId
                        )
                );

        /*
         * ----------------------------------------
         * FIND ALL MATCHES INVOLVING TEAM
         * AT THIS VENUE
         * ----------------------------------------
         */

        List<Match> venueMatches =
                matchRepository.findByVenue_Id(venueId);

        List<Match> teamMatches = venueMatches.stream()
                .filter(match ->
                        match.getTeam1().getId().equals(teamId)
                                || match.getTeam2().getId().equals(teamId)
                )
                .toList();

        if (teamMatches.isEmpty()) {

            throw new BadRequestException(
                    "Team '" + team.getName()
                            + "' has no matches at venue '"
                            + venue.getName() + "'"
            );
        }

        /*
         * ----------------------------------------
         * RESULT COUNTERS
         * ----------------------------------------
         */

        int matches = teamMatches.size();

        int wins = 0;
        int losses = 0;
        int ties = 0;
        int noResults = 0;

        /*
         * ----------------------------------------
         * RUNNING TOTALS
         * ----------------------------------------
         */

        long totalRuns = 0;
        long totalBalls = 0;

        List<Integer> teamRuns = new ArrayList<>();

        /*
         * ----------------------------------------
         * PROCESS MATCHES
         * ----------------------------------------
         */

        for (Match match : teamMatches) {

            String status = match.getMatchStatus();

            /*
             * ------------------------------------
             * MATCH RESULT
             * ------------------------------------
             */

            if ("NO_RESULT".equalsIgnoreCase(status)) {

                noResults++;

            } else if ("COMPLETED".equalsIgnoreCase(status)) {

                if (match.getWinner() != null) {

                    Long winnerId =
                            match.getWinner().getId();

                    if (winnerId.equals(teamId)) {

                        wins++;

                    } else {

                        losses++;
                    }

                } else {

                    String resultDescription =
                            match.getResultDescription();

                    if (resultDescription != null
                            && resultDescription
                            .toLowerCase()
                            .contains("tie")) {

                        ties++;

                    } else {

                        noResults++;
                    }
                }
            } else {

                /*
                 * Any unexpected non-completed status
                 * is treated as no result rather than
                 * incorrectly counting it as a loss.
                 */

                noResults++;
            }

            /*
             * ------------------------------------
             * TEAM MATCH STATISTICS
             *
             * Statistics are only used when the
             * match has valid completed statistics.
             * ------------------------------------
             */

            if (!"COMPLETED".equalsIgnoreCase(status)) {
                continue;
            }

            List<MatchTeamStats> matchStats =
                    matchTeamStatsRepository.findByMatch_Id(
                            match.getId()
                    );

            MatchTeamStats teamStats =
                    matchStats.stream()
                            .filter(stats ->
                                    stats.getTeam() != null
                                            && stats.getTeam()
                                            .getId()
                                            .equals(teamId)
                            )
                            .findFirst()
                            .orElse(null);

            if (teamStats == null) {
                continue;
            }

            /*
             * ------------------------------------
             * RUNS
             * ------------------------------------
             */

            int runs =
                    safeInt(teamStats.getRuns());

            int balls =
                    safeInt(teamStats.getTotalBalls());

            teamRuns.add(runs);

            totalRuns += runs;
            totalBalls += balls;
        }

        /*
         * ----------------------------------------
         * WIN PERCENTAGE
         *
         * Calculated over all team matches,
         * including no-results/ties.
         * ----------------------------------------
         */

        double winPercentage =
                matches == 0
                        ? 0.0
                        : ((double) wins / matches) * 100.0;

        /*
         * ----------------------------------------
         * AVERAGE RUNS
         * ----------------------------------------
         */

        double averageRuns =
                calculateAverage(teamRuns);

        /*
         * ----------------------------------------
         * AGGREGATE RUN RATE
         *
         * Total runs × 6 / total balls
         *
         * This is a weighted/aggregate run rate,
         * unlike averaging individual match rates.
         * ----------------------------------------
         */

        double averageRunRate =
                totalBalls == 0
                        ? 0.0
                        : (totalRuns * 6.0) / totalBalls;

        /*
         * ----------------------------------------
         * BUILD RESPONSE
         * ----------------------------------------
         */

        return TeamVenueAnalyticsResponseDTO.builder()

                .venueId(venue.getId())

                .venueName(venue.getName())

                .teamId(team.getId())

                .teamName(team.getName())

                .teamShortName(team.getShortName())

                .matches(matches)

                .wins(wins)

                .losses(losses)

                .ties(ties)

                .noResults(noResults)

                .winPercentage(
                        roundToTwoDecimals(winPercentage)
                )

                .averageRuns(
                        roundToTwoDecimals(averageRuns)
                )

                .averageRunRate(
                        roundToTwoDecimals(averageRunRate)
                )

                .build();
    }

    /*
     * ----------------------------------------
     * CALCULATE AVERAGE RUNS
     * ----------------------------------------
     */

    private double calculateAverage(
            List<Integer> values
    ) {

        if (values == null || values.isEmpty()) {
            return 0.0;
        }

        double total = 0.0;

        for (Integer value : values) {
            total += safeInt(value);
        }

        return total / values.size();
    }

    /*
     * ----------------------------------------
     * NULL-SAFE INTEGER
     * ----------------------------------------
     */

    private int safeInt(Integer value) {

        return value == null
                ? 0
                : value;
    }

    /*
     * ----------------------------------------
     * ROUND TO TWO DECIMALS
     * ----------------------------------------
     */

    private double roundToTwoDecimals(
            double value
    ) {

        return Math.round(
                value * 100.0
        ) / 100.0;
    }
}