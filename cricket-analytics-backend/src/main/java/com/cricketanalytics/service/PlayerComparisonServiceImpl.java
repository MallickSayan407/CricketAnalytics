package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.PlayerComparisonResponseDTO;
import com.cricketanalytics.analytics.service.PlayerComparisonService;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerStatistics;
import com.cricketanalytics.exception.ResourceNotFoundException;
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
public class PlayerComparisonServiceImpl
        implements PlayerComparisonService {

    private final PlayerRepository playerRepository;

    private final PlayerStatisticsRepository statisticsRepository;


    @Override
    public PlayerComparisonResponseDTO comparePlayers(
            List<Long> playerIds,
            Long competitionId,
            Long seasonId) {

        if (playerIds == null || playerIds.isEmpty()) {

            throw new IllegalArgumentException(
                    "At least one player ID is required"
            );
        }


        /*
         * A comparison requires at least two players.
         */
        if (playerIds.size() < 2) {

            throw new IllegalArgumentException(
                    "At least two player IDs are required for comparison"
            );
        }


        /*
         * Prevent accidental duplicate player IDs.
         */
        List<Long> uniquePlayerIds =
                playerIds.stream()
                        .filter(Objects::nonNull)
                        .distinct()
                        .collect(Collectors.toList());


        if (uniquePlayerIds.size() < 2) {

            throw new IllegalArgumentException(
                    "At least two different player IDs are required"
            );
        }


        List<PlayerComparisonResponseDTO.PlayerComparison>
                comparisons = new ArrayList<>();


        for (Long playerId : uniquePlayerIds) {

            Player player =
                    playerRepository.findById(playerId)
                            .orElseThrow(() ->
                                    new ResourceNotFoundException(
                                            "Player not found with id: "
                                                    + playerId
                                    )
                            );


            List<PlayerStatistics> statistics =
                    statisticsRepository
                            .findByPlayer_Id(playerId);


            /*
             * Select the correct statistics according
             * to competition and season filters.
             */
            statistics = filterStatistics(
                    statistics,
                    competitionId,
                    seasonId
            );


            comparisons.add(
                    buildPlayerComparison(
                            player,
                            statistics
                    )
            );
        }


        return PlayerComparisonResponseDTO
                .builder()
                .players(comparisons)
                .build();
    }


    /*
     * ---------------------------------------------------------
     * STATISTICS FILTERING
     * ---------------------------------------------------------
     *
     * No filters:
     *     Use CAREER statistics only.
     *
     * Competition only:
     *     Aggregate SEASON statistics belonging
     *     to that competition.
     *
     * Competition + season:
     *     Use the matching SEASON statistics.
     *
     * This prevents CAREER + SEASON rows from
     * being double-counted.
     */

    private List<PlayerStatistics> filterStatistics(
            List<PlayerStatistics> statistics,
            Long competitionId,
            Long seasonId) {

        if (statistics == null || statistics.isEmpty()) {
            return new ArrayList<>();
        }


        /*
         * ---------------------------------------------------------
         * NO FILTERS
         * ---------------------------------------------------------
         *
         * Use the player's overall CAREER row.
         */
        if (competitionId == null
                && seasonId == null) {

            return statistics.stream()

                    .filter(stat ->
                            "CAREER".equalsIgnoreCase(
                                    stat.getScope()
                            )
                    )

                    .collect(Collectors.toList());
        }


        /*
         * ---------------------------------------------------------
         * SEASON FILTER WITHOUT COMPETITION
         * ---------------------------------------------------------
         */
        if (competitionId == null
                && seasonId != null) {

            throw new IllegalArgumentException(
                    "Competition ID is required when Season ID is provided"
            );
        }


        /*
         * ---------------------------------------------------------
         * COMPETITION + SEASON
         * ---------------------------------------------------------
         *
         * Example:
         * competitionId = 4
         * seasonId = 30
         *
         * Returns IPL 2007/08 statistics.
         */
        if (seasonId != null) {

            return statistics.stream()

                    .filter(stat ->
                            "SEASON".equalsIgnoreCase(
                                    stat.getScope()
                            )
                    )

                    .filter(stat ->
                            stat.getCompetition() != null
                    )

                    .filter(stat ->
                            Objects.equals(
                                    stat.getCompetition().getId(),
                                    competitionId
                            )
                    )

                    .filter(stat ->
                            stat.getSeason() != null
                    )

                    .filter(stat ->
                            Objects.equals(
                                    stat.getSeason().getId(),
                                    seasonId
                            )
                    )

                    .collect(Collectors.toList());
        }


        /*
         * ---------------------------------------------------------
         * COMPETITION ONLY
         * ---------------------------------------------------------
         *
         * First look for a CAREER row belonging to the
         * requested competition.
         *
         * ODI example:
         *
         * CAREER + International ODI
         *
         * If such a row exists, use it directly.
         */
        List<PlayerStatistics> competitionCareerStats =
                statistics.stream()

                        .filter(stat ->
                                "CAREER".equalsIgnoreCase(
                                        stat.getScope()
                                )
                        )

                        .filter(stat ->
                                stat.getCompetition() != null
                        )

                        .filter(stat ->
                                Objects.equals(
                                        stat.getCompetition().getId(),
                                        competitionId
                                )
                        )

                        .collect(Collectors.toList());


        if (!competitionCareerStats.isEmpty()) {

            return competitionCareerStats;
        }


        /*
         * ---------------------------------------------------------
         * COMPETITION WITHOUT CAREER ROW
         * ---------------------------------------------------------
         *
         * Example:
         *
         * IPL
         *
         * There is no IPL CAREER row in the current database,
         * so aggregate the SEASON rows belonging to that
         * competition.
         */
        return statistics.stream()

                .filter(stat ->
                        "SEASON".equalsIgnoreCase(
                                stat.getScope()
                        )
                )

                .filter(stat ->
                        stat.getCompetition() != null
                )

                .filter(stat ->
                        Objects.equals(
                                stat.getCompetition().getId(),
                                competitionId
                        )
                )

                .collect(Collectors.toList());
    }


    /*
     * ---------------------------------------------------------
     * BUILD PLAYER COMPARISON
     * ---------------------------------------------------------
     */

    private PlayerComparisonResponseDTO.PlayerComparison
    buildPlayerComparison(
            Player player,
            List<PlayerStatistics> statistics) {

        if (statistics.isEmpty()) {

            return PlayerComparisonResponseDTO
                    .PlayerComparison
                    .builder()

                    .playerId(player.getId())

                    .playerName(player.getName())

                    .teamName(
                            player.getTeam() != null
                                    ? player.getTeam().getName()
                                    : null
                    )

                    .teamShortName(
                            player.getTeam() != null
                                    ? player.getTeam().getShortName()
                                    : null
                    )

                    .role(player.getRole())

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


        int matches =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getMatches())
                        )
                        .sum();


        int runs =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getRuns())
                        )
                        .sum();


        int highestScore =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getHighestScore())
                        )
                        .max()
                        .orElse(0);


        int fifties =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getFifties())
                        )
                        .sum();


        int centuries =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getCenturies())
                        )
                        .sum();


        int notOuts =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getNotOuts())
                        )
                        .sum();


        int wickets =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getWickets())
                        )
                        .sum();


        int runsConceded =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getRunsConceded())
                        )
                        .sum();


        int fiveWicketHauls =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getFiveWicketHauls())
                        )
                        .sum();


        int ballsFaced =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getBallsFaced())
                        )
                        .sum();


        int ballsBowled =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(stat.getBallsBowled())
                        )
                        .sum();


        /*
         * Batting average:
         *
         * Runs / dismissals
         *
         * Dismissals = batting innings - not outs
         */
        int dismissals =
                statistics.stream()
                        .mapToInt(stat ->
                                safeInt(
                                        stat.getBattingInnings()
                                )
                                -
                                safeInt(
                                        stat.getNotOuts()
                                )
                        )
                        .sum();


        double battingAverage = 0.0;

        if (dismissals > 0) {

            battingAverage =
                    runs / (double) dismissals;
        } else if (runs > 0) {

            battingAverage = runs;
        }


        /*
         * Strike rate:
         *
         * Runs / balls faced × 100
         */
        double strikeRate = 0.0;

        if (ballsFaced > 0) {

            strikeRate =
                    runs * 100.0
                            / ballsFaced;
        }


        /*
         * Economy:
         *
         * Runs conceded / overs
         *
         * Overs = balls / 6
         */
        double economy = 0.0;

        if (ballsBowled > 0) {

            economy =
                    runsConceded * 6.0
                            / ballsBowled;
        }


        /*
         * Bowling average:
         *
         * Runs conceded / wickets
         */
        double bowlingAverage = 0.0;

        if (wickets > 0) {

            bowlingAverage =
                    runsConceded
                            / (double) wickets;
        }


        return PlayerComparisonResponseDTO
                .PlayerComparison
                .builder()

                .playerId(player.getId())

                .playerName(player.getName())

                .teamName(
                        player.getTeam() != null
                                ? player.getTeam().getName()
                                : null
                )

                .teamShortName(
                        player.getTeam() != null
                                ? player.getTeam().getShortName()
                                : null
                )

                .role(player.getRole())

                .matches(matches)

                .runs(runs)

                .highestScore(highestScore)

                .fifties(fifties)

                .centuries(centuries)

                .notOuts(notOuts)

                .battingAverage(
                        round(battingAverage)
                )

                .strikeRate(
                        round(strikeRate)
                )

                .wickets(wickets)

                .runsConceded(runsConceded)

                .economy(
                        round(economy)
                )

                .bowlingAverage(
                        round(bowlingAverage)
                )

                .fiveWicketHauls(
                        fiveWicketHauls
                )

                .build();
    }


    /*
     * ---------------------------------------------------------
     * HELPERS
     * ---------------------------------------------------------
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