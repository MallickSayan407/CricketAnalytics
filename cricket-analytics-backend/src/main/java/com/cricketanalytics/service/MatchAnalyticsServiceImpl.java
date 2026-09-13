package com.cricketanalytics.service;

import com.cricketanalytics.analytics.dto.MatchAnalyticsResponseDTO;
import com.cricketanalytics.analytics.service.MatchAnalyticsService;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerMatchPerformance;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.PlayerMatchPerformanceRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class MatchAnalyticsServiceImpl
        implements MatchAnalyticsService {

    private final MatchRepository matchRepository;

    private final MatchTeamStatsRepository statsRepository;

    private final PlayerMatchPerformanceRepository performanceRepository;


    // =========================================================
    // MATCH ANALYTICS
    // =========================================================

    @Override
    public MatchAnalyticsResponseDTO getMatchAnalytics(
            Long matchId) {

        Match match = matchRepository.findById(matchId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Match not found with id: "
                                        + matchId
                        )
                );


        List<MatchTeamStats> teamStats =
                statsRepository.findByMatch_Id(matchId);


        List<PlayerMatchPerformance> performances =
                performanceRepository.findByMatch_Id(matchId);


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


        return MatchAnalyticsResponseDTO.builder()

                .matchId(match.getId())

                .matchDate(
                        match.getMatchDate() != null
                                ? match.getMatchDate().toString()
                                : null
                )

                .matchStatus(match.getMatchStatus())

                .stage(match.getStage())

                .competitionName(
                        match.getCompetition() != null
                                ? match.getCompetition().getName()
                                : null
                )

                .competitionFormat(
                        match.getCompetition() != null
                                ? match.getCompetition().getFormat()
                                : null
                )

                .seasonName(
                        match.getSeason() != null
                                ? match.getSeason().getName()
                                : null
                )

                .venueName(
                        match.getVenue() != null
                                ? match.getVenue().getName()
                                : null
                )

                .venueCity(
                        match.getVenue() != null
                                ? match.getVenue().getCity()
                                : null
                )

                .venueCountry(
                        match.getVenue() != null
                                ? match.getVenue().getCountry()
                                : null
                )

                .team1(
                        mapTeamStats(team1Stats)
                )

                .team2(
                        mapTeamStats(team2Stats)
                )

                .tossWinner(
                        match.getTossWinner() != null
                                ? match.getTossWinner().getName()
                                : null
                )

                .tossDecision(match.getTossDecision())

                .winner(
                        match.getWinner() != null
                                ? match.getWinner().getName()
                                : null
                )

                .resultDescription(
                        match.getResultDescription()
                )

                .playerPerformances(
                        performances.stream()
                                .map(this::mapPlayerPerformance)
                                .toList()
                )

                .build();
    }


    // =========================================================
    // FIND TEAM STATS
    // =========================================================

    private MatchTeamStats findTeamStats(
            List<MatchTeamStats> teamStats,
            Long teamId) {

        return teamStats.stream()

                .filter(stat ->
                        stat.getTeam() != null
                                && stat.getTeam()
                                .getId()
                                .equals(teamId)
                )

                .findFirst()

                .orElse(null);
    }


    // =========================================================
    // TEAM STATISTICS MAPPING
    // =========================================================

    private MatchAnalyticsResponseDTO.TeamMatchSummary
    mapTeamStats(
            MatchTeamStats stats) {

        if (stats == null) {
            return null;
        }


        return MatchAnalyticsResponseDTO
                .TeamMatchSummary
                .builder()

                .teamId(
                        stats.getTeam() != null
                                ? stats.getTeam().getId()
                                : null
                )

                .teamName(
                        stats.getTeam() != null
                                ? stats.getTeam().getName()
                                : null
                )

                .teamShortName(
                        stats.getTeam() != null
                                ? stats.getTeam().getShortName()
                                : null
                )

                .runs(stats.getRuns())

                .wickets(stats.getWickets())

                .totalBalls(stats.getTotalBalls())

                .overs(
                        formatOvers(
                                stats.getTotalBalls()
                        )
                )

                .fours(stats.getFours())

                .sixes(stats.getSixes())

                .extras(stats.getExtras())

                .runRate(
                        calculateRunRate(
                                stats.getRuns(),
                                stats.getTotalBalls()
                        )
                )

                .build();
    }


    // =========================================================
    // PLAYER PERFORMANCE MAPPING
    // =========================================================

    private MatchAnalyticsResponseDTO.PlayerMatchSummary
    mapPlayerPerformance(
            PlayerMatchPerformance performance) {

        Player player =
                performance.getPlayer();


        return MatchAnalyticsResponseDTO
                .PlayerMatchSummary
                .builder()

                .playerId(
                        player != null
                                ? player.getId()
                                : null
                )

                .playerName(
                        player != null
                                ? player.getName()
                                : null
                )

                .role(
                        player != null
                                ? player.getRole()
                                : null
                )

                /*
                 * IMPORTANT:
                 *
                 * Prefer the historical team stored on
                 * PlayerMatchPerformance.
                 *
                 * This is necessary for players who changed
                 * IPL franchises over time.
                 */
                .teamName(
                        performance.getTeam() != null
                                ? performance.getTeam().getName()
                                : (
                                    player != null
                                            && player.getTeam() != null
                                            ? player.getTeam().getName()
                                            : null
                                )
                )


                // -------------------------------------------------
                // Batting
                // -------------------------------------------------

                .battingRuns(
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

                .battingStrikeRate(
                        performance.getBattingStrikeRate()
                )

                .notOut(
                        performance.getNotOut()
                )


                // -------------------------------------------------
                // Bowling
                // -------------------------------------------------

                .ballsBowled(
                        performance.getBallsBowled()
                )

                .oversBowled(
                        formatOvers(
                                performance.getBallsBowled()
                        )
                )

                .runsConceded(
                        performance.getRunsConceded()
                )

                .wickets(
                        performance.getWickets()
                )

                .bowlingEconomy(
                        performance.getBowlingEconomy()
                )

                .maidens(
                        performance.getMaidens()
                )

                .build();
    }


    // =========================================================
    // OVERS FORMATTER
    // =========================================================

    private String formatOvers(Integer totalBalls) {

        if (totalBalls == null || totalBalls < 0) {
            return "0.0";
        }


        int overs = totalBalls / 6;

        int balls = totalBalls % 6;


        return overs + "." + balls;
    }


    // =========================================================
    // RUN RATE
    // =========================================================

    private Double calculateRunRate(
            Integer runs,
            Integer totalBalls) {

        if (runs == null
                || totalBalls == null
                || totalBalls <= 0) {

            return 0.0;
        }


        double runRate =
                runs * 6.0 / totalBalls;


        return round(runRate);
    }


    // =========================================================
    // ROUND TO 2 DECIMAL PLACES
    // =========================================================

    private double round(double value) {

        return Math.round(value * 100.0)
                / 100.0;
    }
}