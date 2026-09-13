package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.SeasonAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.SeasonAnalyticsService;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Season;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.SeasonRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class SeasonAnalyticsServiceImpl
        implements SeasonAnalyticsService {

    private final SeasonRepository seasonRepository;

    private final MatchRepository matchRepository;

    private final MatchTeamStatsRepository matchTeamStatsRepository;

    @Override
    public SeasonAnalyticsResponseDTO getSeasonAnalytics(
            Long seasonId
    ) {

        Season season = seasonRepository.findById(seasonId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Season not found with id: " + seasonId
                        )
                );

        List<Match> matches =
                matchRepository.findBySeason_Id(seasonId);

        int completedMatches = 0;
        int tiedMatches = 0;
        int noResultMatches = 0;

        int totalRuns = 0;
        int totalFours = 0;
        int totalSixes = 0;

        int highestTeamScore = 0;
        Integer lowestTeamScore = null;

        /*
         * Used for aggregate run rate.
         *
         * Aggregate Run Rate =
         *
         * Total Runs × 6 / Total Balls
         */
        int totalBalls = 0;

        List<Integer> matchRuns = new ArrayList<>();

        for (Match match : matches) {

            String matchStatus = match.getMatchStatus();

            /*
             * Result classification must be performed
             * against ALL matches, not only completed matches.
             */
            if ("NO_RESULT".equalsIgnoreCase(matchStatus)) {

                noResultMatches++;

                continue;
            }

            if (!"COMPLETED".equalsIgnoreCase(matchStatus)) {

                continue;
            }

            completedMatches++;

            /*
             * Completed match result classification.
             */
            if (match.getWinner() == null) {

                String resultDescription =
                        match.getResultDescription();

                if (resultDescription != null
                        && resultDescription
                        .toLowerCase()
                        .contains("tie")) {

                    tiedMatches++;

                } else {

                    noResultMatches++;
                }
            }

            /*
             * Match/team statistics should only contribute
             * to scoring analytics for completed matches.
             */
            List<MatchTeamStats> teamStats =
                    matchTeamStatsRepository.findByMatch_Id(
                            match.getId()
                    );

            int currentMatchRuns = 0;

            for (MatchTeamStats stats : teamStats) {

                int runs = safeInt(stats.getRuns());

                int balls = safeInt(stats.getTotalBalls());

                currentMatchRuns += runs;

                totalRuns += runs;

                totalBalls += balls;

                totalFours += safeInt(stats.getFours());

                totalSixes += safeInt(stats.getSixes());

                if (runs > highestTeamScore) {

                    highestTeamScore = runs;
                }

                if (lowestTeamScore == null
                        || runs < lowestTeamScore) {

                    lowestTeamScore = runs;
                }
            }

            /*
             * One entry represents one completed match.
             */
            if (!teamStats.isEmpty()) {

                matchRuns.add(currentMatchRuns);
            }
        }

        /*
         * Aggregate season run rate:
         *
         * Total Runs × 6 / Total Balls
         *
         * This is preferable to taking an unweighted
         * average of individual team run rates.
         */
        double averageRunRate =
                calculateAggregateRunRate(
                        totalRuns,
                        totalBalls
                );

        return SeasonAnalyticsResponseDTO.builder()

                .seasonId(season.getId())

                .seasonName(season.getName())

                .startYear(season.getStartYear())

                .endYear(season.getEndYear())

                .competitionId(
                        season.getCompetition().getId()
                )

                .competitionName(
                        season.getCompetition().getName()
                )

                .competitionType(
                        season.getCompetition().getType()
                )

                .competitionFormat(
                        season.getCompetition().getFormat()
                )

                .totalMatches(matches.size())

                .completedMatches(completedMatches)

                .tiedMatches(tiedMatches)

                .noResultMatches(noResultMatches)

                .totalRuns(totalRuns)

                .averageMatchRuns(
                        calculateAverage(matchRuns)
                )

                .highestTeamScore(highestTeamScore)

                .lowestTeamScore(
                        lowestTeamScore == null
                                ? 0
                                : lowestTeamScore
                )

                .totalFours(totalFours)

                .totalSixes(totalSixes)

                .averageRunRate(averageRunRate)

                .build();
    }

    private double calculateAverage(
            List<Integer> values
    ) {

        if (values == null || values.isEmpty()) {

            return 0.0;
        }

        int total = 0;

        for (Integer value : values) {

            total += safeInt(value);
        }

        return roundToTwoDecimals(
                (double) total / values.size()
        );
    }

    private double calculateAggregateRunRate(
            int totalRuns,
            int totalBalls
    ) {

        if (totalBalls == 0) {

            return 0.0;
        }

        return roundToTwoDecimals(
                (double) totalRuns * 6 / totalBalls
        );
    }

    private int safeInt(Integer value) {

        return value == null ? 0 : value;
    }

    private double roundToTwoDecimals(
            double value
    ) {

        return Math.round(value * 100.0) / 100.0;
    }
}