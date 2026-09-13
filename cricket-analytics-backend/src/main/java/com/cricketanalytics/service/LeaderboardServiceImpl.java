package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.LeaderboardResponseDTO;
import com.cricketanalytics.analytics.service.LeaderboardService;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerMatchPerformance;
import com.cricketanalytics.entity.PlayerStatistics;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.repository.PlayerMatchPerformanceRepository;
import com.cricketanalytics.repository.PlayerStatisticsRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class LeaderboardServiceImpl implements LeaderboardService {

    private static final int CAREER_MIN_BATTING_INNINGS = 20;
    private static final int SEASON_MIN_BATTING_INNINGS = 5;

    private final PlayerStatisticsRepository statisticsRepository;
    private final PlayerMatchPerformanceRepository performanceRepository;

    // ============================================================
    // TOP RUN SCORERS
    // ============================================================

    @Override
    public List<LeaderboardResponseDTO> getTopRunScorers(
            Long competitionId,
            Long seasonId
    ) {

        return buildLeaderboard(
                getStatistics(competitionId, seasonId),
                Comparator.comparing(
                        PlayerStatistics::getRuns,
                        Comparator.nullsLast(Comparator.reverseOrder())
                ),
                competitionId,
                seasonId
        );
    }

    // ============================================================
    // TOP BATTING AVERAGE
    // ============================================================

    @Override
    public List<LeaderboardResponseDTO> getTopBattingAverage(
            Long competitionId,
            Long seasonId
    ) {

        List<PlayerStatistics> statistics =
                getStatistics(competitionId, seasonId);

        statistics = applyBattingQualification(
                statistics,
                seasonId != null
        );

        return buildLeaderboard(
                statistics,
                Comparator.comparing(
                        PlayerStatistics::getBattingAverage,
                        Comparator.nullsLast(Comparator.reverseOrder())
                ),
                competitionId,
                seasonId
        );
    }

    // ============================================================
    // TOP STRIKE RATE
    // ============================================================

    @Override
    public List<LeaderboardResponseDTO> getTopStrikeRate(
            Long competitionId,
            Long seasonId
    ) {

        List<PlayerStatistics> statistics =
                getStatistics(competitionId, seasonId);

        statistics = applyBattingQualification(
                statistics,
                seasonId != null
        );

        return buildLeaderboard(
                statistics,
                Comparator.comparing(
                        PlayerStatistics::getStrikeRate,
                        Comparator.nullsLast(Comparator.reverseOrder())
                ),
                competitionId,
                seasonId
        );
    }

    // ============================================================
    // TOP CENTURIES
    // ============================================================

    @Override
    public List<LeaderboardResponseDTO> getTopCenturies(
            Long competitionId,
            Long seasonId
    ) {

        return buildLeaderboard(
                getStatistics(competitionId, seasonId),
                Comparator.comparing(
                        PlayerStatistics::getCenturies,
                        Comparator.nullsLast(Comparator.reverseOrder())
                ),
                competitionId,
                seasonId
        );
    }

    // ============================================================
    // TOP WICKET TAKERS
    // ============================================================

    @Override
    public List<LeaderboardResponseDTO> getTopWickets(
            Long competitionId,
            Long seasonId
    ) {

        return buildLeaderboard(
                getStatistics(competitionId, seasonId),
                Comparator.comparing(
                        PlayerStatistics::getWickets,
                        Comparator.nullsLast(Comparator.reverseOrder())
                ),
                competitionId,
                seasonId
        );
    }

    // ============================================================
    // GET STATISTICS
    // ============================================================

    private List<PlayerStatistics> getStatistics(
            Long competitionId,
            Long seasonId
    ) {

        /*
         * A season must always belong to a competition.
         */
        if (seasonId != null && competitionId == null) {

            throw new IllegalArgumentException(
                    "competitionId is required when seasonId is provided"
            );
        }

        /*
         * ========================================================
         * CASE 1:
         * Competition + Season
         *
         * Return only SEASON statistics for that season.
         * ========================================================
         */

        if (competitionId != null && seasonId != null) {

            return statisticsRepository
                    .findByCompetition_IdAndSeason_Id(
                            competitionId,
                            seasonId
                    )
                    .stream()
                    .filter(this::isSeasonStatistics)
                    .toList();
        }

        /*
         * ========================================================
         * CASE 2:
         * Competition only
         *
         * International competitions:
         *     use CAREER rows.
         *
         * IPL:
         *     aggregate SEASON rows.
         * ========================================================
         */

        if (competitionId != null) {

            List<PlayerStatistics> competitionStatistics =
                    statisticsRepository.findByCompetition_Id(
                            competitionId
                    );

            /*
             * If genuine CAREER rows exist, use them.
             */
            List<PlayerStatistics> careerStatistics =
                    competitionStatistics.stream()
                            .filter(this::isCareerStatistics)
                            .toList();

            if (!careerStatistics.isEmpty()) {
                return careerStatistics;
            }

            /*
             * IPL currently has no CAREER rows.
             *
             * Therefore aggregate all IPL SEASON rows by player.
             */
            List<PlayerStatistics> seasonStatistics =
                    competitionStatistics.stream()
                            .filter(this::isSeasonStatistics)
                            .toList();

            return aggregateStatisticsByPlayer(
                    seasonStatistics
            );
        }

        /*
         * ========================================================
         * CASE 3:
         * No filters
         *
         * Use existing CAREER records.
         * ========================================================
         */

        return statisticsRepository.findByScope("CAREER");
    }

    // ============================================================
    // APPLY BATTING QUALIFICATION
    // ============================================================

    private List<PlayerStatistics> applyBattingQualification(
            List<PlayerStatistics> statistics,
            boolean seasonRequest
    ) {

        int minimumInnings =
                seasonRequest
                        ? SEASON_MIN_BATTING_INNINGS
                        : CAREER_MIN_BATTING_INNINGS;

        return statistics.stream()
                .filter(statisticsRow ->
                        safeInt(statisticsRow.getBattingInnings())
                                >= minimumInnings
                )
                .toList();
    }

    // ============================================================
    // AGGREGATE SEASON STATISTICS BY PLAYER
    // ============================================================

    private List<PlayerStatistics> aggregateStatisticsByPlayer(
            List<PlayerStatistics> seasonStatistics
    ) {

        Map<Long, PlayerStatistics> aggregated =
                new LinkedHashMap<>();

        for (PlayerStatistics season : seasonStatistics) {

            if (season.getPlayer() == null) {
                continue;
            }

            Long playerId =
                    season.getPlayer().getId();

            if (!aggregated.containsKey(playerId)) {

                aggregated.put(
                        playerId,
                        copyStatistics(season)
                );

            } else {

                PlayerStatistics total =
                        aggregated.get(playerId);

                addStatistics(
                        total,
                        season
                );
            }
        }

        return new ArrayList<>(aggregated.values());
    }

    // ============================================================
    // COPY FIRST STATISTICS ROW
    // ============================================================

    private PlayerStatistics copyStatistics(
            PlayerStatistics source
    ) {

        return PlayerStatistics.builder()

                .player(source.getPlayer())
                .competition(source.getCompetition())
                .season(source.getSeason())
                .scope("CAREER")

                .matches(
                        safeInt(source.getMatches())
                )

                .battingInnings(
                        safeInt(source.getBattingInnings())
                )

                .runs(
                        safeInt(source.getRuns())
                )

                .ballsFaced(
                        safeInt(source.getBallsFaced())
                )

                .highestScore(
                        safeInt(source.getHighestScore())
                )

                .notOuts(
                        safeInt(source.getNotOuts())
                )

                .fours(
                        safeInt(source.getFours())
                )

                .sixes(
                        safeInt(source.getSixes())
                )

                .fifties(
                        safeInt(source.getFifties())
                )

                .centuries(
                        safeInt(source.getCenturies())
                )

                .bowlingInnings(
                        safeInt(source.getBowlingInnings())
                )

                .ballsBowled(
                        safeInt(source.getBallsBowled())
                )

                .wickets(
                        safeInt(source.getWickets())
                )

                .runsConceded(
                        safeInt(source.getRunsConceded())
                )

                .bestBowlingWickets(
                        safeInt(source.getBestBowlingWickets())
                )

                .fiveWicketHauls(
                        safeInt(source.getFiveWicketHauls())
                )

                .battingAverage(0.0)
                .strikeRate(0.0)
                .economy(0.0)
                .bowlingAverage(0.0)

                .build();
    }

    // ============================================================
    // ADD SEASON STATISTICS
    // ============================================================

    private void addStatistics(
            PlayerStatistics total,
            PlayerStatistics season
    ) {

        /*
         * -------------------------
         * Batting
         * -------------------------
         */

        total.setMatches(
                safeInt(total.getMatches())
                        + safeInt(season.getMatches())
        );

        total.setBattingInnings(
                safeInt(total.getBattingInnings())
                        + safeInt(season.getBattingInnings())
        );

        total.setRuns(
                safeInt(total.getRuns())
                        + safeInt(season.getRuns())
        );

        total.setBallsFaced(
                safeInt(total.getBallsFaced())
                        + safeInt(season.getBallsFaced())
        );

        total.setNotOuts(
                safeInt(total.getNotOuts())
                        + safeInt(season.getNotOuts())
        );

        total.setFours(
                safeInt(total.getFours())
                        + safeInt(season.getFours())
        );

        total.setSixes(
                safeInt(total.getSixes())
                        + safeInt(season.getSixes())
        );

        total.setFifties(
                safeInt(total.getFifties())
                        + safeInt(season.getFifties())
        );

        total.setCenturies(
                safeInt(total.getCenturies())
                        + safeInt(season.getCenturies())
        );

        total.setHighestScore(
                Math.max(
                        safeInt(total.getHighestScore()),
                        safeInt(season.getHighestScore())
                )
        );

        /*
         * -------------------------
         * Bowling
         * -------------------------
         */

        total.setBowlingInnings(
                safeInt(total.getBowlingInnings())
                        + safeInt(season.getBowlingInnings())
        );

        total.setBallsBowled(
                safeInt(total.getBallsBowled())
                        + safeInt(season.getBallsBowled())
        );

        total.setWickets(
                safeInt(total.getWickets())
                        + safeInt(season.getWickets())
        );

        total.setRunsConceded(
                safeInt(total.getRunsConceded())
                        + safeInt(season.getRunsConceded())
        );

        total.setFiveWicketHauls(
                safeInt(total.getFiveWicketHauls())
                        + safeInt(season.getFiveWicketHauls())
        );

        total.setBestBowlingWickets(
                Math.max(
                        safeInt(total.getBestBowlingWickets()),
                        safeInt(season.getBestBowlingWickets())
                )
        );

        recalculateDerivedStatistics(total);
    }

    // ============================================================
    // RECALCULATE DERIVED STATISTICS
    // ============================================================

    private void recalculateDerivedStatistics(
            PlayerStatistics statistics
    ) {

        int runs =
                safeInt(statistics.getRuns());

        int battingInnings =
                safeInt(statistics.getBattingInnings());

        int notOuts =
                safeInt(statistics.getNotOuts());

        int ballsFaced =
                safeInt(statistics.getBallsFaced());

        int runsConceded =
                safeInt(statistics.getRunsConceded());

        int wickets =
                safeInt(statistics.getWickets());

        int ballsBowled =
                safeInt(statistics.getBallsBowled());

        /*
         * Batting average.
         */

        int dismissedInnings =
                battingInnings - notOuts;

        double battingAverage = 0.0;

        if (dismissedInnings > 0) {

            battingAverage =
                    (double) runs / dismissedInnings;
        }

        /*
         * Strike rate.
         */

        double strikeRate = 0.0;

        if (ballsFaced > 0) {

            strikeRate =
                    ((double) runs / ballsFaced) * 100.0;
        }

        /*
         * Bowling economy.
         */

        double economy = 0.0;

        if (ballsBowled > 0) {

            economy =
                    ((double) runsConceded * 6.0)
                            / ballsBowled;
        }

        /*
         * Bowling average.
         */

        double bowlingAverage = 0.0;

        if (wickets > 0) {

            bowlingAverage =
                    (double) runsConceded / wickets;
        }

        statistics.setBattingAverage(
                roundTwo(battingAverage)
        );

        statistics.setStrikeRate(
                roundTwo(strikeRate)
        );

        statistics.setEconomy(
                roundTwo(economy)
        );

        statistics.setBowlingAverage(
                roundTwo(bowlingAverage)
        );
    }

    // ============================================================
    // SCOPE HELPERS
    // ============================================================

    private boolean isCareerStatistics(
            PlayerStatistics statistics
    ) {

        return statistics != null
                && statistics.getScope() != null
                && "CAREER".equalsIgnoreCase(
                statistics.getScope()
        );
    }

    private boolean isSeasonStatistics(
            PlayerStatistics statistics
    ) {

        return statistics != null
                && statistics.getScope() != null
                && "SEASON".equalsIgnoreCase(
                statistics.getScope()
        );
    }

    // ============================================================
    // BUILD LEADERBOARD
    // ============================================================

    private List<LeaderboardResponseDTO> buildLeaderboard(
            List<PlayerStatistics> statistics,
            Comparator<PlayerStatistics> comparator,
            Long competitionId,
            Long seasonId
    ) {

        List<LeaderboardResponseDTO> leaderboard =
                statistics.stream()

                        .filter(statisticsRow ->
                                statisticsRow != null
                                        && statisticsRow.getPlayer() != null
                        )

                        .sorted(comparator)

                        .map(statisticsRow ->
                                mapToResponse(
                                        statisticsRow,
                                        competitionId,
                                        seasonId
                                )
                        )

                        .toList();

        /*
         * Assign rank after sorting.
         */

        for (int i = 0; i < leaderboard.size(); i++) {

            leaderboard
                    .get(i)
                    .setRank(i + 1);
        }

        return leaderboard;
    }

    // ============================================================
    // ENTITY -> DTO
    // ============================================================

    private LeaderboardResponseDTO mapToResponse(
            PlayerStatistics statistics,
            Long competitionId,
            Long seasonId
    ) {

        Player player = statistics.getPlayer();

        /*
         * Find the historically relevant team.
         */
        Team historicalTeam =
                findHistoricalTeam(
                        player,
                        competitionId,
                        seasonId
                );

        /*
         * If historical team cannot be resolved,
         * fall back to the player's default team.
         */
        if (historicalTeam == null) {
            historicalTeam = player.getTeam();
        }

        return LeaderboardResponseDTO.builder()

                .playerId(
                        player.getId()
                )

                .playerName(
                        player.getName()
                )

                .playerRole(
                        player.getRole()
                )

                .teamName(
                        historicalTeam != null
                                ? historicalTeam.getName()
                                : null
                )

                .teamShortName(
                        historicalTeam != null
                                ? historicalTeam.getShortName()
                                : null
                )

                .matches(
                        statistics.getMatches()
                )

                .runs(
                        statistics.getRuns()
                )

                .battingAverage(
                        statistics.getBattingAverage()
                )

                .strikeRate(
                        statistics.getStrikeRate()
                )

                .centuries(
                        statistics.getCenturies()
                )

                .fifties(
                        statistics.getFifties()
                )

                .wickets(
                        statistics.getWickets()
                )

                .bowlingAverage(
                        statistics.getBowlingAverage()
                )

                .economy(
                        statistics.getEconomy()
                )

                .build();
    }

    // ============================================================
    // HISTORICAL TEAM RESOLUTION
    // ============================================================

    private Team findHistoricalTeam(
            Player player,
            Long competitionId,
            Long seasonId
    ) {

        /*
         * No competition filter:
         * use the player's normal/default team.
         */
        if (competitionId == null) {
            return player.getTeam();
        }

        List<PlayerMatchPerformance> performances =
                performanceRepository.findByPlayer_Id(
                        player.getId()
                );

        /*
         * Count appearances for each team after applying
         * competition and optional season filters.
         */
        Map<Long, TeamAppearance> teamAppearances =
                new LinkedHashMap<>();

        for (PlayerMatchPerformance performance : performances) {

            if (performance == null
                    || performance.getMatch() == null
                    || performance.getTeam() == null) {
                continue;
            }

            if (performance.getMatch().getCompetition() == null) {
                continue;
            }

            Long performanceCompetitionId =
                    performance.getMatch()
                            .getCompetition()
                            .getId();

            if (!competitionId.equals(performanceCompetitionId)) {
                continue;
            }

            if (seasonId != null) {

                if (performance.getMatch().getSeason() == null) {
                    continue;
                }

                Long performanceSeasonId =
                        performance.getMatch()
                                .getSeason()
                                .getId();

                if (!seasonId.equals(performanceSeasonId)) {
                    continue;
                }
            }

            Team team = performance.getTeam();

            Long teamId = team.getId();

            TeamAppearance appearance =
                    teamAppearances.computeIfAbsent(
                            teamId,
                            id -> new TeamAppearance(team)
                    );

            appearance.increment();
        }

        /*
         * No historical performance was found.
         */
        if (teamAppearances.isEmpty()) {
            return null;
        }

        /*
         * Choose the team with the greatest number of
         * appearances.
         *
         * If two teams have the same number of appearances,
         * retain the first encountered team.
         */
        return teamAppearances.values()
                .stream()
                .max(
                        Comparator.comparingInt(
                                TeamAppearance::getAppearances
                        )
                )
                .map(TeamAppearance::getTeam)
                .orElse(null);
    }

    // ============================================================
    // TEAM APPEARANCE HELPER
    // ============================================================

    private static class TeamAppearance {

        private final Team team;
        private int appearances;

        private TeamAppearance(Team team) {
            this.team = team;
            this.appearances = 0;
        }

        private void increment() {
            appearances++;
        }

        private Team getTeam() {
            return team;
        }

        private int getAppearances() {
            return appearances;
        }
    }

    // ============================================================
    // UTILITY METHODS
    // ============================================================

    private int safeInt(Integer value) {
        return value != null ? value : 0;
    }

    private double roundTwo(double value) {
        return Math.round(value * 100.0) / 100.0;
    }
}