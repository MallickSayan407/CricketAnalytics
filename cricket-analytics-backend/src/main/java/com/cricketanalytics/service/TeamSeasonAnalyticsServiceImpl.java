package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.TeamSeasonStandingResponseDTO;
import com.cricketanalytics.analytics.service.TeamSeasonAnalyticsService;
import com.cricketanalytics.entity.Competition;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Season;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.SeasonRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class TeamSeasonAnalyticsServiceImpl implements TeamSeasonAnalyticsService {

    private final SeasonRepository seasonRepository;
    private final MatchRepository matchRepository;
    private final MatchTeamStatsRepository matchTeamStatsRepository;

    @Override
    public List<TeamSeasonStandingResponseDTO> getSeasonStandings(Long seasonId) {

        Season season = seasonRepository.findById(seasonId)
                .orElseThrow(() ->
                        new IllegalArgumentException(
                                "Season not found with id: " + seasonId
                        )
                );

        List<Match> matches = matchRepository.findBySeason_Id(seasonId);

        Map<Long, StandingData> standings = new HashMap<>();

        /*
         * ================================================================
         * INITIALIZE TEAMS
         * ================================================================
         *
         * Use Match.team1 and Match.team2 as the source of truth.
         *
         * This is important for NO_RESULT matches where MatchTeamStats
         * may be incomplete or absent.
         */

        for (Match match : matches) {

            // Exclude matches that do not count toward official standings.
            if (Boolean.FALSE.equals(match.getCountedInStandings())) {
                continue;
            }

            // IPL standings contain League-stage matches only.
            if (isIplSeason(season) && !isLeagueStage(match)) {
                continue;
            }

            Team team1 = match.getTeam1();
            Team team2 = match.getTeam2();

            if (team1 != null) {
                standings.putIfAbsent(
                        team1.getId(),
                        new StandingData(
                                team1.getId(),
                                team1.getName(),
                                team1.getShortName()
                        )
                );
            }

            if (team2 != null) {
                standings.putIfAbsent(
                        team2.getId(),
                        new StandingData(
                                team2.getId(),
                                team2.getName(),
                                team2.getShortName()
                        )
                );
            }
        }

        /*
         * ================================================================
         * PROCESS MATCHES
         * ================================================================
         */

        for (Match match : matches) {

            // Exclude matches that do not count toward official standings.
            if (Boolean.FALSE.equals(match.getCountedInStandings())) {
                continue;
            }

            // IPL standings contain League-stage matches only.
            if (isIplSeason(season) && !isLeagueStage(match)) {
                continue;
            }

            Team team1 = match.getTeam1();
            Team team2 = match.getTeam2();

            if (team1 == null || team2 == null) {
                continue;
            }

            StandingData standing1 = standings.get(team1.getId());
            StandingData standing2 = standings.get(team2.getId());

            if (standing1 == null || standing2 == null) {
                continue;
            }

            /*
             * Every eligible match counts as a match played.
             */
            standing1.matches++;
            standing2.matches++;

            List<MatchTeamStats> matchStats =
                    matchTeamStatsRepository.findByMatch_Id(match.getId());

            /*
             * ============================================================
             * NO RESULT
             * ============================================================
             *
             * Both teams receive one point.
             *
             * No win/loss.
             *
             * No NRR contribution.
             */

            if ("NO_RESULT".equalsIgnoreCase(match.getMatchStatus())) {

                standing1.noResults++;
                standing2.noResults++;

                standing1.points++;
                standing2.points++;

                continue;
            }

            /*
             * ============================================================
             * TRUE TIE
             * ============================================================
             */

            if (isTrueTie(match)) {

                standing1.ties++;
                standing2.ties++;

                standing1.points++;
                standing2.points++;

                continue;
            }

            /*
             * ============================================================
             * COMPLETED MATCH
             * ============================================================
             */

            Team winner = match.getWinner();

            if (winner != null) {

                if (winner.getId().equals(team1.getId())) {

                    standing1.wins++;
                    standing1.points += 2;
                    standing2.losses++;

                } else if (winner.getId().equals(team2.getId())) {

                    standing2.wins++;
                    standing2.points += 2;
                    standing1.losses++;
                }
            }

            /*
             * ============================================================
             * NRR
             * ============================================================
             *
             * NRR requires valid statistics for both teams.
             *
             * allocatedBalls is used rather than totalBalls.
             */

            if (matchStats == null || matchStats.size() < 2) {
                continue;
            }

            MatchTeamStats stats1 = null;
            MatchTeamStats stats2 = null;

            for (MatchTeamStats stat : matchStats) {

                if (stat == null || stat.getTeam() == null) {
                    continue;
                }

                Long statTeamId = stat.getTeam().getId();

                if (statTeamId.equals(team1.getId())) {
                    stats1 = stat;

                } else if (statTeamId.equals(team2.getId())) {
                    stats2 = stat;
                }
            }

            if (stats1 == null || stats2 == null) {
                continue;
            }

            updateNrrStats(
                    standing1,
                    standing2,
                    stats1,
                    stats2
            );
        }

        /*
         * ================================================================
         * BUILD RESPONSE
         * ================================================================
         */

        List<TeamSeasonStandingResponseDTO> response = new ArrayList<>();

        Competition competition = season.getCompetition();

        Long competitionId =
                competition != null
                        ? competition.getId()
                        : null;

        String competitionName =
                competition != null
                        ? competition.getName()
                        : null;

        Long currentSeasonId = season.getId();

        String seasonName = season.getName();

        for (StandingData standing : standings.values()) {

            double netRunRate = calculateNetRunRate(standing);

            double winPercentage =
                    calculateWinPercentage(standing);

            double runRate =
                    calculateRunRate(
                            standing.runsScored,
                            standing.ballsFaced
                    );

            double bowlingRate =
                    calculateRunRate(
                            standing.runsConceded,
                            standing.ballsBowled
                    );

            TeamSeasonStandingResponseDTO dto =
                    TeamSeasonStandingResponseDTO.builder()
                            .rank(null)

                            .seasonId(currentSeasonId)
                            .seasonName(seasonName)

                            .competitionId(competitionId)
                            .competitionName(competitionName)

                            .teamId(standing.teamId)
                            .teamName(standing.teamName)
                            .teamShortName(standing.teamShortName)

                            .matches(standing.matches)
                            .wins(standing.wins)
                            .losses(standing.losses)
                            .ties(standing.ties)
                            .noResults(standing.noResults)
                            .points(standing.points)

                            .winPercentage(winPercentage)

                            .runsScored((int) standing.runsScored)
                            .ballsFaced((int) standing.ballsFaced)

                            .runsConceded((int) standing.runsConceded)
                            .ballsBowled((int) standing.ballsBowled)

                            .runRate(runRate)
                            .bowlingRate(bowlingRate)

                            .netRunRate(netRunRate)

                            .build();

            response.add(dto);
        }

        /*
         * ================================================================
         * OFFICIAL IPL-STYLE SORTING
         * ================================================================
         *
         * 1. Points DESC
         * 2. Wins DESC
         * 3. NRR DESC
         * 4. Team name ASC
         */

        response.sort(
                Comparator
                        .comparing(
                                TeamSeasonStandingResponseDTO::getPoints,
                                Comparator.reverseOrder()
                        )
                        .thenComparing(
                                TeamSeasonStandingResponseDTO::getWins,
                                Comparator.reverseOrder()
                        )
                        .thenComparing(
                                TeamSeasonStandingResponseDTO::getNetRunRate,
                                Comparator.reverseOrder()
                        )
                        .thenComparing(
                                TeamSeasonStandingResponseDTO::getTeamName,
                                String.CASE_INSENSITIVE_ORDER
                        )
        );

        /*
         * ================================================================
         * ASSIGN RANK
         * ================================================================
         *
         * Rank is assigned AFTER sorting.
         */

        for (int i = 0; i < response.size(); i++) {
            response.get(i).setRank(i + 1);
        }

        return response;
    }

    /**
     * Determines whether the season belongs to the IPL.
     */
    private boolean isIplSeason(Season season) {

        if (season == null) {
            return false;
        }

        Competition competition = season.getCompetition();

        if (competition == null) {
            return false;
        }

        String competitionName = competition.getName();
        String competitionFormat = competition.getFormat();

        return "Indian Premier League".equalsIgnoreCase(competitionName)
                || "IPL".equalsIgnoreCase(competitionFormat);
    }

    /**
     * Only League-stage matches are included in IPL standings.
     */
    private boolean isLeagueStage(Match match) {

        if (match == null) {
            return false;
        }

        String stage = match.getStage();

        return stage == null
                || stage.isBlank()
                || "League".equalsIgnoreCase(stage);
    }

    /**
     * Determines whether the match is a genuine tie.
     *
     * A Super Over match has a winner and therefore is not treated
     * as a normal tied match.
     */
    private boolean isTrueTie(Match match) {

        if (match == null) {
            return false;
        }

        if (match.getWinner() != null) {
            return false;
        }

        if (!"COMPLETED".equalsIgnoreCase(match.getMatchStatus())
                && !"TIED".equalsIgnoreCase(match.getMatchStatus())) {

            return false;
        }

        String resultDescription =
                match.getResultDescription();

        if (resultDescription == null) {
            return "TIED".equalsIgnoreCase(
                    match.getMatchStatus()
            );
        }

        String description =
                resultDescription.toLowerCase();

        if (description.contains("super over")) {
            return false;
        }

        return description.contains("tie")
                || description.contains("tied")
                || "TIED".equalsIgnoreCase(
                        match.getMatchStatus()
                );
    }

    /**
     * Adds batting and bowling values needed for NRR.
     */
    private void updateNrrStats(
            StandingData standing1,
            StandingData standing2,
            MatchTeamStats stats1,
            MatchTeamStats stats2
    ) {

        // Team 1 batting contribution.
        standing1.runsScored += safeInt(
                stats1.getRuns()
        );

        standing1.ballsFaced += getAllocatedBalls(
                stats1
        );

        // Team 1 bowling contribution.
        standing1.runsConceded += safeInt(
                stats2.getRuns()
        );

        standing1.ballsBowled += getAllocatedBalls(
                stats2
        );

        // Team 2 batting contribution.
        standing2.runsScored += safeInt(
                stats2.getRuns()
        );

        standing2.ballsFaced += getAllocatedBalls(
                stats2
        );

        // Team 2 bowling contribution.
        standing2.runsConceded += safeInt(
                stats1.getRuns()
        );

        standing2.ballsBowled += getAllocatedBalls(
                stats1
        );
    }

    /**
     * Gets allocated balls.
     *
     * For legacy rows where allocatedBalls is zero,
     * totalBalls is used as a fallback.
     */
    private int getAllocatedBalls(MatchTeamStats stats) {

        if (stats == null) {
            return 0;
        }

        Integer allocatedBalls =
                stats.getAllocatedBalls();

        if (allocatedBalls != null && allocatedBalls > 0) {
            return allocatedBalls;
        }

        Integer totalBalls =
                stats.getTotalBalls();

        return totalBalls != null
                ? totalBalls
                : 0;
    }

    /**
     * Calculates Net Run Rate.
     *
     * NRR =
     *
     * (runs scored / overs faced)
     *
     * -
     *
     * (runs conceded / overs bowled)
     */
    private double calculateNetRunRate(
            StandingData standing
    ) {

        if (standing == null) {
            return 0.0;
        }

        if (standing.ballsFaced <= 0
                || standing.ballsBowled <= 0) {

            return 0.0;
        }

        double oversFaced =
                standing.ballsFaced / 6.0;

        double oversBowled =
                standing.ballsBowled / 6.0;

        double battingRunRate =
                standing.runsScored / oversFaced;

        double bowlingRunRate =
                standing.runsConceded / oversBowled;

        double nrr =
                battingRunRate - bowlingRunRate;

        return BigDecimal
                .valueOf(nrr)
                .setScale(
                        3,
                        RoundingMode.HALF_UP
                )
                .doubleValue();
    }

    /**
     * Calculates winning percentage.
     *
     * wins / matches * 100
     */
    private double calculateWinPercentage(
            StandingData standing
    ) {

        if (standing == null || standing.matches <= 0) {
            return 0.0;
        }

        double percentage =
                ((double) standing.wins / standing.matches) * 100.0;

        return BigDecimal
                .valueOf(percentage)
                .setScale(
                        2,
                        RoundingMode.HALF_UP
                )
                .doubleValue();
    }

    /**
     * Calculates a run rate from runs and allocated balls.
     *
     * Rate = runs / overs
     */
    private double calculateRunRate(
            long runs,
            long balls
    ) {

        if (balls <= 0) {
            return 0.0;
        }

        double overs = balls / 6.0;

        double rate = runs / overs;

        return BigDecimal
                .valueOf(rate)
                .setScale(
                        2,
                        RoundingMode.HALF_UP
                )
                .doubleValue();
    }

    /**
     * Safely converts nullable Integer values to int.
     */
    private int safeInt(Integer value) {
        return value != null ? value : 0;
    }

    /**
     * Internal object used while calculating standings.
     */
    private static class StandingData {

        private final Long teamId;
        private final String teamName;
        private final String teamShortName;

        private int matches;
        private int wins;
        private int losses;
        private int ties;
        private int noResults;
        private int points;

        private long runsScored;
        private long runsConceded;

        private long ballsFaced;
        private long ballsBowled;

        private StandingData(
                Long teamId,
                String teamName,
                String teamShortName
        ) {
            this.teamId = teamId;
            this.teamName = teamName;
            this.teamShortName = teamShortName;
        }
    }
}