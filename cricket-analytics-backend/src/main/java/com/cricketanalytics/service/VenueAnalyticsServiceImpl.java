package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.VenueAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.VenueAnalyticsService;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.entity.Venue;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.VenueRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class VenueAnalyticsServiceImpl implements VenueAnalyticsService {

    private final VenueRepository venueRepository;
    private final MatchRepository matchRepository;
    private final MatchTeamStatsRepository matchTeamStatsRepository;

    @Override
    public VenueAnalyticsResponseDTO getVenueAnalytics(Long venueId) {

        Venue venue = venueRepository.findById(venueId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Venue not found with id: " + venueId
                        )
                );

        List<Match> matches =
                matchRepository.findByVenue_Id(venueId);

        int completedMatches = 0;
        int team1Wins = 0;
        int team2Wins = 0;
        int tiedMatches = 0;
        int noResultMatches = 0;

        int totalFours = 0;
        int totalSixes = 0;

        List<Integer> firstInningsScores = new ArrayList<>();
        List<Integer> secondInningsScores = new ArrayList<>();
        List<Integer> allTeamScores = new ArrayList<>();

        long totalRuns = 0;
        long totalBalls = 0;

        for (Match match : matches) {

            /*
             * ----------------------------------------
             * MATCH RESULT
             * ----------------------------------------
             */

            String status = match.getMatchStatus();

            if ("NO_RESULT".equalsIgnoreCase(status)) {

                noResultMatches++;

            } else if ("COMPLETED".equalsIgnoreCase(status)) {

                completedMatches++;

                if (match.getWinner() != null) {

                    Long winnerId = match.getWinner().getId();

                    if (winnerId.equals(match.getTeam1().getId())) {
                        team1Wins++;
                    } else if (winnerId.equals(match.getTeam2().getId())) {
                        team2Wins++;
                    }

                } else {

                    String resultDescription =
                            match.getResultDescription();

                    if (resultDescription != null) {

                        String result =
                                resultDescription.toLowerCase();

                        if (result.contains("tie")) {
                            tiedMatches++;
                        }
                    }
                }
            }

            /*
             * ----------------------------------------
             * TEAM MATCH STATISTICS
             *
             * Only completed matches are used for
             * scoring/innings/rate calculations.
             * ----------------------------------------
             */

            if (!"COMPLETED".equalsIgnoreCase(status)) {
                continue;
            }

            List<MatchTeamStats> teamStats =
                    matchTeamStatsRepository.findByMatch_Id(
                            match.getId()
                    );

            MatchTeamStats team1Stats =
                    findTeamStats(
                            teamStats,
                            match.getTeam1().getId()
                    );

            MatchTeamStats team2Stats =
                    findTeamStats(
                            teamStats,
                            match.getTeam2().getId()
                    );

            /*
             * ----------------------------------------
             * DETERMINE ACTUAL BATTING ORDER
             *
             * If toss winner chose BAT:
             *     toss winner bats first.
             *
             * If toss winner chose FIELD:
             *     other team bats first.
             * ----------------------------------------
             */

            MatchTeamStats firstTeamStats = null;
            MatchTeamStats secondTeamStats = null;

            Team tossWinner = match.getTossWinner();
            String tossDecision = match.getTossDecision();

            if (tossWinner != null && tossDecision != null) {

                if ("bat".equalsIgnoreCase(tossDecision)) {

                    if (tossWinner.getId()
                            .equals(match.getTeam1().getId())) {

                        firstTeamStats = team1Stats;
                        secondTeamStats = team2Stats;

                    } else if (tossWinner.getId()
                            .equals(match.getTeam2().getId())) {

                        firstTeamStats = team2Stats;
                        secondTeamStats = team1Stats;
                    }

                } else if ("field".equalsIgnoreCase(tossDecision)) {

                    if (tossWinner.getId()
                            .equals(match.getTeam1().getId())) {

                        firstTeamStats = team2Stats;
                        secondTeamStats = team1Stats;

                    } else if (tossWinner.getId()
                            .equals(match.getTeam2().getId())) {

                        firstTeamStats = team1Stats;
                        secondTeamStats = team2Stats;
                    }
                }
            }

            /*
             * ----------------------------------------
             * FALLBACK
             *
             * If toss information is unexpectedly
             * unavailable, preserve the old behavior
             * rather than losing the match statistics.
             * ----------------------------------------
             */

            if (firstTeamStats == null || secondTeamStats == null) {

                firstTeamStats = team1Stats;
                secondTeamStats = team2Stats;
            }

            /*
             * ----------------------------------------
             * FIRST INNINGS
             * ----------------------------------------
             */

            if (firstTeamStats != null) {

                int runs =
                        safeInt(firstTeamStats.getRuns());

                firstInningsScores.add(runs);
                allTeamScores.add(runs);

                totalRuns += runs;
                totalBalls +=
                        safeInt(firstTeamStats.getTotalBalls());

                totalFours +=
                        safeInt(firstTeamStats.getFours());

                totalSixes +=
                        safeInt(firstTeamStats.getSixes());
            }

            /*
             * ----------------------------------------
             * SECOND INNINGS
             * ----------------------------------------
             */

            if (secondTeamStats != null) {

                int runs =
                        safeInt(secondTeamStats.getRuns());

                secondInningsScores.add(runs);
                allTeamScores.add(runs);

                totalRuns += runs;
                totalBalls +=
                        safeInt(secondTeamStats.getTotalBalls());

                totalFours +=
                        safeInt(secondTeamStats.getFours());

                totalSixes +=
                        safeInt(secondTeamStats.getSixes());
            }
        }

        /*
         * ----------------------------------------
         * BUILD RESPONSE
         * ----------------------------------------
         */

        double averageRunRate =
                totalBalls == 0
                        ? 0.0
                        : roundToTwoDecimals(
                                totalRuns * 6.0 / totalBalls
                        );

        return VenueAnalyticsResponseDTO.builder()

                .venueId(venue.getId())

                .venueName(venue.getName())

                .city(venue.getCity())

                .country(venue.getCountry())

                .capacity(venue.getCapacity())

                .totalMatches(matches.size())

                .completedMatches(completedMatches)

                .team1Wins(team1Wins)

                .team2Wins(team2Wins)

                .tiedMatches(tiedMatches)

                .noResultMatches(noResultMatches)

                .averageFirstInningsScore(
                        calculateAverage(
                                firstInningsScores
                        )
                )

                .averageSecondInningsScore(
                        calculateAverage(
                                secondInningsScores
                        )
                )

                .averageMatchRuns(
                        calculateAverageMatchRuns(
                                firstInningsScores,
                                secondInningsScores
                        )
                )

                .highestTeamScore(
                        calculateHighest(
                                allTeamScores
                        )
                )

                .lowestTeamScore(
                        calculateLowest(
                                allTeamScores
                        )
                )

                .averageRunRate(averageRunRate)

                .totalFours(totalFours)

                .totalSixes(totalSixes)

                .build();
    }

    private MatchTeamStats findTeamStats(
            List<MatchTeamStats> teamStats,
            Long teamId
    ) {

        return teamStats.stream()
                .filter(stats ->
                        stats.getTeam() != null
                                && stats.getTeam()
                                .getId()
                                .equals(teamId)
                )
                .findFirst()
                .orElse(null);
    }

    private Double calculateAverage(
            List<Integer> values
    ) {

        if (values == null || values.isEmpty()) {
            return 0.0;
        }

        double total = 0.0;

        for (Integer value : values) {
            total += safeInt(value);
        }

        return roundToTwoDecimals(
                total / values.size()
        );
    }

    private Double calculateAverageMatchRuns(
            List<Integer> firstInningsScores,
            List<Integer> secondInningsScores
    ) {

        if (firstInningsScores.isEmpty()
                || secondInningsScores.isEmpty()) {

            return 0.0;
        }

        int matchCount =
                Math.min(
                        firstInningsScores.size(),
                        secondInningsScores.size()
                );

        double totalMatchRuns = 0.0;

        for (int i = 0; i < matchCount; i++) {

            totalMatchRuns +=
                    safeInt(firstInningsScores.get(i))
                            +
                    safeInt(secondInningsScores.get(i));
        }

        return roundToTwoDecimals(
                totalMatchRuns / matchCount
        );
    }

    private Integer calculateHighest(
            List<Integer> values
    ) {

        if (values == null || values.isEmpty()) {
            return 0;
        }

        return values.stream()
                .mapToInt(this::safeInt)
                .max()
                .orElse(0);
    }

    private Integer calculateLowest(
            List<Integer> values
    ) {

        if (values == null || values.isEmpty()) {
            return 0;
        }

        return values.stream()
                .mapToInt(this::safeInt)
                .min()
                .orElse(0);
    }

    private int safeInt(Integer value) {
        return value == null ? 0 : value;
    }

    private double roundToTwoDecimals(
            double value
    ) {

        return Math.round(
                value * 100.0
        ) / 100.0;
    }
}