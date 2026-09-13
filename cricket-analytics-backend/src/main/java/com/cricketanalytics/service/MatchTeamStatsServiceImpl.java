package com.cricketanalytics.service;

import com.cricketanalytics.dto.MatchTeamStatsRequestDTO;
import com.cricketanalytics.dto.MatchTeamStatsResponseDTO;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.MatchTeamStats;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.exception.DuplicateResourceException;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.MatchTeamStatsRepository;
import com.cricketanalytics.repository.TeamRepository;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class MatchTeamStatsServiceImpl
        implements MatchTeamStatsService {

    private final MatchTeamStatsRepository statsRepository;

    private final MatchRepository matchRepository;

    private final TeamRepository teamRepository;

    @Override
    public MatchTeamStatsResponseDTO createStats(
            MatchTeamStatsRequestDTO request) {

        Match match = findMatchById(request.getMatchId());

        Team team = findTeamById(request.getTeamId());

        validateTeamParticipatesInMatch(team, match);

        if (statsRepository.existsByMatch_IdAndTeam_Id(
                request.getMatchId(),
                request.getTeamId())) {

            throw new DuplicateResourceException(
                    "Statistics already exist for this team in the match"
            );
        }

        MatchTeamStats stats = MatchTeamStats.builder()
                .match(match)
                .team(team)
                .runs(request.getRuns())
                .wickets(request.getWickets())
                .totalBalls(request.getTotalBalls())
                .fours(request.getFours())
                .sixes(request.getSixes())
                .extras(request.getExtras())
                .runRate(request.getRunRate())
                .build();

        MatchTeamStats savedStats =
                statsRepository.save(stats);

        return mapToResponse(savedStats);
    }

    @Override
    public List<MatchTeamStatsResponseDTO> getAllStats() {

        return statsRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public MatchTeamStatsResponseDTO getStatsById(Long id) {

        MatchTeamStats stats =
                statsRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Match team statistics not found with id: "
                                                + id
                        ));

        return mapToResponse(stats);
    }

    @Override
    public List<MatchTeamStatsResponseDTO> getStatsByMatch(
            Long matchId) {

        findMatchById(matchId);

        return statsRepository.findByMatch_Id(matchId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<MatchTeamStatsResponseDTO> getStatsByTeam(
            Long teamId) {

        findTeamById(teamId);

        return statsRepository.findByTeam_Id(teamId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public MatchTeamStatsResponseDTO getStatsByMatchAndTeam(
            Long matchId,
            Long teamId) {

        findMatchById(matchId);

        findTeamById(teamId);

        MatchTeamStats stats =
                statsRepository.findByMatch_IdAndTeam_Id(
                                matchId,
                                teamId
                        )
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Statistics not found for matchId="
                                                + matchId
                                                + " and teamId="
                                                + teamId
                        ));

        return mapToResponse(stats);
    }

    @Override
    public MatchTeamStatsResponseDTO updateStats(
            Long id,
            MatchTeamStatsRequestDTO request) {

        MatchTeamStats stats =
                statsRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Match team statistics not found with id: "
                                                + id
                        ));

        Match match =
                findMatchById(request.getMatchId());

        Team team =
                findTeamById(request.getTeamId());

        validateTeamParticipatesInMatch(
                team,
                match
        );

        statsRepository
                .findByMatch_IdAndTeam_Id(
                        request.getMatchId(),
                        request.getTeamId()
                )
                .ifPresent(existingStats -> {

                    if (!existingStats.getId().equals(id)) {

                        throw new DuplicateResourceException(
                                "Statistics already exist for this team in the match"
                        );
                    }
                });

        stats.setMatch(match);
        stats.setTeam(team);
        stats.setRuns(request.getRuns());
        stats.setWickets(request.getWickets());
        stats.setTotalBalls(request.getTotalBalls());
        stats.setFours(request.getFours());
        stats.setSixes(request.getSixes());
        stats.setExtras(request.getExtras());
        stats.setRunRate(request.getRunRate());

        MatchTeamStats updatedStats =
                statsRepository.save(stats);

        return mapToResponse(updatedStats);
    }

    @Override
    public void deleteStats(Long id) {

        if (!statsRepository.existsById(id)) {

            throw new ResourceNotFoundException(
                    "Match team statistics not found with id: "
                            + id
            );
        }

        statsRepository.deleteById(id);
    }

    // =========================================================
    // Helper methods
    // =========================================================

    private Match findMatchById(Long matchId) {

        return matchRepository.findById(matchId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Match not found with id: "
                                        + matchId
                        ));
    }

    private Team findTeamById(Long teamId) {

        return teamRepository.findById(teamId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Team not found with id: "
                                        + teamId
                        ));
    }

    private void validateTeamParticipatesInMatch(
            Team team,
            Match match) {

        boolean participates =
                team.getId().equals(match.getTeam1().getId())
                        || team.getId().equals(match.getTeam2().getId());

        if (!participates) {

            throw new IllegalArgumentException(
                    "Team does not participate in the selected match"
            );
        }
    }

    private MatchTeamStatsResponseDTO mapToResponse(
            MatchTeamStats stats) {

        Match match = stats.getMatch();

        Team team = stats.getTeam();

        return MatchTeamStatsResponseDTO.builder()
                .id(stats.getId())

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

                .runs(stats.getRuns())

                .wickets(stats.getWickets())

                .totalBalls(stats.getTotalBalls())

                .overs(
                        formatOvers(stats.getTotalBalls())
                )

                .fours(stats.getFours())

                .sixes(stats.getSixes())

                .extras(stats.getExtras())

                .runRate(stats.getRunRate())

                .build();
    }

    /**
     * Converts total balls into cricket overs notation.
     *
     * 272 balls = 45.2 overs
     * 297 balls = 49.3 overs
     */
    private String formatOvers(Integer totalBalls) {

        if (totalBalls == null || totalBalls < 0) {
            return "0.0";
        }

        int overs = totalBalls / 6;

        int balls = totalBalls % 6;

        return overs + "." + balls;
    }
}