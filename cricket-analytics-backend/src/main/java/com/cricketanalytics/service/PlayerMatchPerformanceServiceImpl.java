package com.cricketanalytics.service;

import com.cricketanalytics.dto.PlayerMatchPerformanceRequestDTO;
import com.cricketanalytics.dto.PlayerMatchPerformanceResponseDTO;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerMatchPerformance;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.exception.BadRequestException;
import com.cricketanalytics.exception.DuplicateResourceException;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.PlayerMatchPerformanceRepository;
import com.cricketanalytics.repository.PlayerRepository;
import com.cricketanalytics.repository.TeamRepository;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PlayerMatchPerformanceServiceImpl
        implements PlayerMatchPerformanceService {

    private final PlayerMatchPerformanceRepository performanceRepository;
    private final PlayerRepository playerRepository;
    private final MatchRepository matchRepository;
    private final TeamRepository teamRepository;


    // =========================================================
    // CREATE
    // =========================================================

    @Override
    public PlayerMatchPerformanceResponseDTO createPerformance(
            PlayerMatchPerformanceRequestDTO request) {

        Player player =
                findPlayerById(request.getPlayerId());

        Match match =
                findMatchById(request.getMatchId());

        Team team =
                findTeamById(request.getTeamId());

        /*
         * IMPORTANT:
         *
         * We validate the team represented by the player
         * in THIS match.
         *
         * We do NOT use player.getTeam() because Player.team
         * represents the player's current/default team and may
         * be different from their historical IPL team.
         */
        validateTeamParticipatesInMatch(
                team,
                match
        );

        if (performanceRepository.existsByPlayer_IdAndMatch_Id(
                request.getPlayerId(),
                request.getMatchId())) {

            throw new DuplicateResourceException(
                    "Performance already exists for this player in the match"
            );
        }

        PlayerMatchPerformance performance =
                PlayerMatchPerformance.builder()
                        .player(player)
                        .match(match)
                        .team(team)

                        // Batting
                        .battingRuns(request.getBattingRuns())
                        .ballsFaced(request.getBallsFaced())
                        .fours(request.getFours())
                        .sixes(request.getSixes())
                        .notOut(request.getNotOut())

                        // Bowling
                        .ballsBowled(request.getBallsBowled())
                        .runsConceded(request.getRunsConceded())
                        .wickets(request.getWickets())
                        .maidens(request.getMaidens())

                        .build();

        calculateDerivedStatistics(performance);

        PlayerMatchPerformance savedPerformance =
                performanceRepository.save(performance);

        return mapToResponse(savedPerformance);
    }


    // =========================================================
    // GET ALL
    // =========================================================

    @Override
    public List<PlayerMatchPerformanceResponseDTO>
    getAllPerformances() {

        return performanceRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // GET BY ID
    // =========================================================

    @Override
    public PlayerMatchPerformanceResponseDTO
    getPerformanceById(Long id) {

        PlayerMatchPerformance performance =
                performanceRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Player match performance not found with id: "
                                                + id
                                )
                        );

        return mapToResponse(performance);
    }


    // =========================================================
    // GET BY PLAYER
    // =========================================================

    @Override
    public List<PlayerMatchPerformanceResponseDTO>
    getPerformancesByPlayer(Long playerId) {

        findPlayerById(playerId);

        return performanceRepository
                .findByPlayer_Id(playerId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // GET BY MATCH
    // =========================================================

    @Override
    public List<PlayerMatchPerformanceResponseDTO>
    getPerformancesByMatch(Long matchId) {

        findMatchById(matchId);

        return performanceRepository
                .findByMatch_Id(matchId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // GET BY PLAYER + MATCH
    // =========================================================

    @Override
    public PlayerMatchPerformanceResponseDTO
    getPerformanceByPlayerAndMatch(
            Long playerId,
            Long matchId) {

        findPlayerById(playerId);
        findMatchById(matchId);

        PlayerMatchPerformance performance =
                performanceRepository
                        .findByPlayer_IdAndMatch_Id(
                                playerId,
                                matchId
                        )
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Performance not found for playerId="
                                                + playerId
                                                + " and matchId="
                                                + matchId
                                )
                        );

        return mapToResponse(performance);
    }


    // =========================================================
    // UPDATE
    // =========================================================

    @Override
    public PlayerMatchPerformanceResponseDTO
    updatePerformance(
            Long id,
            PlayerMatchPerformanceRequestDTO request) {

        PlayerMatchPerformance performance =
                performanceRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Player match performance not found with id: "
                                                + id
                                )
                        );

        Player player =
                findPlayerById(request.getPlayerId());

        Match match =
                findMatchById(request.getMatchId());

        Team team =
                findTeamById(request.getTeamId());

        /*
         * Validate the supplied historical team against
         * the selected match.
         */
        validateTeamParticipatesInMatch(
                team,
                match
        );

        performanceRepository
                .findByPlayer_IdAndMatch_Id(
                        request.getPlayerId(),
                        request.getMatchId()
                )
                .ifPresent(existingPerformance -> {

                    if (!existingPerformance
                            .getId()
                            .equals(id)) {

                        throw new DuplicateResourceException(
                                "Performance already exists for this player in the match"
                        );
                    }
                });


        // Relationships
        performance.setPlayer(player);
        performance.setMatch(match);
        performance.setTeam(team);


        // Batting
        performance.setBattingRuns(
                request.getBattingRuns()
        );

        performance.setBallsFaced(
                request.getBallsFaced()
        );

        performance.setFours(
                request.getFours()
        );

        performance.setSixes(
                request.getSixes()
        );

        performance.setNotOut(
                request.getNotOut()
        );


        // Bowling
        performance.setBallsBowled(
                request.getBallsBowled()
        );

        performance.setRunsConceded(
                request.getRunsConceded()
        );

        performance.setWickets(
                request.getWickets()
        );

        performance.setMaidens(
                request.getMaidens()
        );


        // Calculate derived values
        calculateDerivedStatistics(performance);


        PlayerMatchPerformance updatedPerformance =
                performanceRepository.save(performance);

        return mapToResponse(updatedPerformance);
    }


    // =========================================================
    // DELETE
    // =========================================================

    @Override
    public void deletePerformance(Long id) {

        if (!performanceRepository.existsById(id)) {

            throw new ResourceNotFoundException(
                    "Player match performance not found with id: "
                            + id
            );
        }

        performanceRepository.deleteById(id);
    }


    // =========================================================
    // DERIVED STATISTICS
    // =========================================================

    private void calculateDerivedStatistics(
            PlayerMatchPerformance performance) {

        int battingRuns =
                safeInt(performance.getBattingRuns());

        int ballsFaced =
                safeInt(performance.getBallsFaced());

        int runsConceded =
                safeInt(performance.getRunsConceded());

        int ballsBowled =
                safeInt(performance.getBallsBowled());


        // ---------------------------------------------------------
        // Batting Strike Rate
        // ---------------------------------------------------------

        double battingStrikeRate = 0.0;

        if (ballsFaced > 0) {

            battingStrikeRate =
                    ((double) battingRuns / ballsFaced)
                            * 100.0;
        }

        performance.setBattingStrikeRate(
                roundToTwoDecimals(battingStrikeRate)
        );


        // ---------------------------------------------------------
        // Bowling Economy
        // ---------------------------------------------------------

        double bowlingEconomy = 0.0;

        if (ballsBowled > 0) {

            double overs =
                    (double) ballsBowled / 6.0;

            bowlingEconomy =
                    (double) runsConceded / overs;
        }

        performance.setBowlingEconomy(
                roundToTwoDecimals(bowlingEconomy)
        );
    }


    // =========================================================
    // VALIDATION HELPERS
    // =========================================================

    private Player findPlayerById(Long playerId) {

        return playerRepository.findById(playerId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Player not found with id: "
                                        + playerId
                        )
                );
    }


    private Match findMatchById(Long matchId) {

        return matchRepository.findById(matchId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Match not found with id: "
                                        + matchId
                        )
                );
    }


    private Team findTeamById(Long teamId) {

        return teamRepository.findById(teamId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: "
                                        + teamId
                        )
                );
    }


    /**
     * Validates that the selected team actually participated
     * in the selected match.
     *
     * This is intentionally based on the Team supplied for
     * this performance rather than Player.team.
     *
     * This is necessary because IPL players can represent
     * different franchises across different seasons.
     */
    private void validateTeamParticipatesInMatch(
            Team team,
            Match match) {

        if (team == null) {

            throw new BadRequestException(
                    "Team is required for player match performance"
            );
        }

        if (match == null) {

            throw new BadRequestException(
                    "Match is required for player match performance"
            );
        }

        if (match.getTeam1() == null
                || match.getTeam2() == null) {

            throw new BadRequestException(
                    "Selected match does not have two participating teams"
            );
        }

        Long teamId =
                team.getId();

        Long team1Id =
                match.getTeam1().getId();

        Long team2Id =
                match.getTeam2().getId();

        boolean participates =
                teamId != null
                        && (
                        teamId.equals(team1Id)
                                || teamId.equals(team2Id)
                );

        if (!participates) {

            throw new BadRequestException(
                    "Selected team does not participate in the selected match"
            );
        }
    }


    // =========================================================
    // UTILITY METHODS
    // =========================================================

    private int safeInt(Integer value) {

        return value == null ? 0 : value;
    }


    private double roundToTwoDecimals(
            double value) {

        return Math.round(value * 100.0)
                / 100.0;
    }


    /*
     * Convert total balls into cricket overs.
     *
     * Examples:
     *
     * 60 balls → 10.0
     * 61 balls → 10.1
     * 65 balls → 10.5
     * 72 balls → 12.0
     */
    private String formatOvers(
            Integer totalBalls) {

        if (totalBalls == null
                || totalBalls < 0) {

            return "0.0";
        }

        int overs =
                totalBalls / 6;

        int balls =
                totalBalls % 6;

        return overs + "." + balls;
    }


    // =========================================================
    // ENTITY → RESPONSE DTO
    // =========================================================

    private PlayerMatchPerformanceResponseDTO
    mapToResponse(
            PlayerMatchPerformance performance) {

        Player player =
                performance.getPlayer();

        Match match =
                performance.getMatch();

        Team team =
                performance.getTeam();

        return PlayerMatchPerformanceResponseDTO
                .builder()

                .id(
                        performance.getId()
                )


                // -------------------------------------------------
                // Player
                // -------------------------------------------------

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

                .playerRole(
                        player != null
                                ? player.getRole()
                                : null
                )


                // -------------------------------------------------
                // Team represented in this match
                // -------------------------------------------------

                .teamId(
                        team != null
                                ? team.getId()
                                : null
                )

                .teamName(
                        team != null
                                ? team.getName()
                                : null
                )

                .teamShortName(
                        team != null
                                ? team.getShortName()
                                : null
                )


                // -------------------------------------------------
                // Match
                // -------------------------------------------------

                .matchId(
                        match != null
                                ? match.getId()
                                : null
                )

                .matchDate(
                        match != null
                                && match.getMatchDate() != null
                                ? match.getMatchDate().toString()
                                : null
                )


                // -------------------------------------------------
                // Competition
                // -------------------------------------------------

                .competitionName(
                        match != null
                                && match.getCompetition() != null
                                ? match.getCompetition().getName()
                                : null
                )

                .competitionFormat(
                        match != null
                                && match.getCompetition() != null
                                ? match.getCompetition().getFormat()
                                : null
                )


                // -------------------------------------------------
                // Team 1
                // -------------------------------------------------

                .team1Id(
                        match != null
                                && match.getTeam1() != null
                                ? match.getTeam1().getId()
                                : null
                )

                .team1Name(
                        match != null
                                && match.getTeam1() != null
                                ? match.getTeam1().getName()
                                : null
                )

                .team1ShortName(
                        match != null
                                && match.getTeam1() != null
                                ? match.getTeam1().getShortName()
                                : null
                )


                // -------------------------------------------------
                // Team 2
                // -------------------------------------------------

                .team2Id(
                        match != null
                                && match.getTeam2() != null
                                ? match.getTeam2().getId()
                                : null
                )

                .team2Name(
                        match != null
                                && match.getTeam2() != null
                                ? match.getTeam2().getName()
                                : null
                )

                .team2ShortName(
                        match != null
                                && match.getTeam2() != null
                                ? match.getTeam2().getShortName()
                                : null
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
}