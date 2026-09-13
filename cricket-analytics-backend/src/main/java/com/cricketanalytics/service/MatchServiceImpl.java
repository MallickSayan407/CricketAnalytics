package com.cricketanalytics.service;

import com.cricketanalytics.dto.MatchRequestDTO;
import com.cricketanalytics.dto.MatchResponseDTO;
import com.cricketanalytics.entity.Competition;
import com.cricketanalytics.entity.Match;
import com.cricketanalytics.entity.Season;
import com.cricketanalytics.entity.Team;
import com.cricketanalytics.entity.Venue;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.CompetitionRepository;
import com.cricketanalytics.repository.MatchRepository;
import com.cricketanalytics.repository.SeasonRepository;
import com.cricketanalytics.repository.TeamRepository;
import com.cricketanalytics.repository.VenueRepository;
import com.cricketanalytics.service.MatchService;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

@Service
@RequiredArgsConstructor
public class MatchServiceImpl implements MatchService {

    private final MatchRepository matchRepository;
    private final CompetitionRepository competitionRepository;
    private final SeasonRepository seasonRepository;
    private final TeamRepository teamRepository;
    private final VenueRepository venueRepository;

    @Override
    public MatchResponseDTO createMatch(MatchRequestDTO request) {

        Competition competition =
                findCompetitionById(request.getCompetitionId());

        Season season =
                findSeasonById(request.getSeasonId());

        Venue venue =
                findVenueById(request.getVenueId());

        Team team1 =
                findTeamById(request.getTeam1Id());

        Team team2 =
                findTeamById(request.getTeam2Id());

        validateTeams(team1, team2);

        validateSeasonBelongsToCompetition(
                season,
                competition
        );

        Team tossWinner = null;

        if (request.getTossWinnerTeamId() != null) {

            tossWinner =
                    findTeamById(request.getTossWinnerTeamId());

            validateTeamParticipates(
                    tossWinner,
                    team1,
                    team2,
                    "Toss winner"
            );
        }

        Team winner = null;

        if (request.getWinnerTeamId() != null) {

            winner =
                    findTeamById(request.getWinnerTeamId());

            validateTeamParticipates(
                    winner,
                    team1,
                    team2,
                    "Winner"
            );
        }

        Match match = Match.builder()
                .matchDate(request.getMatchDate())
                .matchStatus(request.getMatchStatus())
                .tossDecision(request.getTossDecision())
                .resultDescription(request.getResultDescription())
                .competition(competition)
                .season(season)
                .venue(venue)
                .team1(team1)
                .team2(team2)
                .tossWinner(tossWinner)
                .winner(winner)
                .build();

        Match savedMatch = matchRepository.save(match);

        return mapToResponse(savedMatch);
    }

    @Override
    public List<MatchResponseDTO> getAllMatches() {

        return matchRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public MatchResponseDTO getMatchById(Long id) {

        Match match = matchRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Match not found with id: " + id
                        )
                );

        return mapToResponse(match);
    }

    @Override
    public List<MatchResponseDTO> getMatchesByCompetition(
            Long competitionId) {

        findCompetitionById(competitionId);

        return matchRepository
                .findByCompetition_Id(competitionId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<MatchResponseDTO> getMatchesBySeason(
            Long seasonId) {

        findSeasonById(seasonId);

        return matchRepository
                .findBySeason_Id(seasonId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<MatchResponseDTO> getMatchesByVenue(
            Long venueId) {

        findVenueById(venueId);

        return matchRepository
                .findByVenue_Id(venueId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<MatchResponseDTO> getMatchesByTeam(
            Long teamId) {

        findTeamById(teamId);

        return matchRepository
                .findByTeam1_IdOrTeam2_Id(
                        teamId,
                        teamId
                )
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public List<MatchResponseDTO> getMatchesBetweenDates(
            LocalDate startDate,
            LocalDate endDate) {

        if (startDate.isAfter(endDate)) {

            throw new IllegalArgumentException(
                    "Start date cannot be after end date"
            );
        }

        return matchRepository
                .findByMatchDateBetween(
                        startDate,
                        endDate
                )
                .stream()
                .map(this::mapToResponse)
                .toList();
    }

    @Override
    public MatchResponseDTO updateMatch(
            Long id,
            MatchRequestDTO request) {

        Match match = matchRepository.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Match not found with id: " + id
                        )
                );

        Competition competition =
                findCompetitionById(
                        request.getCompetitionId()
                );

        Season season =
                findSeasonById(
                        request.getSeasonId()
                );

        Venue venue =
                findVenueById(
                        request.getVenueId()
                );

        Team team1 =
                findTeamById(
                        request.getTeam1Id()
                );

        Team team2 =
                findTeamById(
                        request.getTeam2Id()
                );

        validateTeams(team1, team2);

        validateSeasonBelongsToCompetition(
                season,
                competition
        );

        Team tossWinner = null;

        if (request.getTossWinnerTeamId() != null) {

            tossWinner =
                    findTeamById(
                            request.getTossWinnerTeamId()
                    );

            validateTeamParticipates(
                    tossWinner,
                    team1,
                    team2,
                    "Toss winner"
            );
        }

        Team winner = null;

        if (request.getWinnerTeamId() != null) {

            winner =
                    findTeamById(
                            request.getWinnerTeamId()
                    );

            validateTeamParticipates(
                    winner,
                    team1,
                    team2,
                    "Winner"
            );
        }

        match.setMatchDate(request.getMatchDate());
        match.setMatchStatus(request.getMatchStatus());
        match.setTossDecision(request.getTossDecision());
        match.setResultDescription(
                request.getResultDescription()
        );

        match.setCompetition(competition);
        match.setSeason(season);
        match.setVenue(venue);

        match.setTeam1(team1);
        match.setTeam2(team2);

        match.setTossWinner(tossWinner);
        match.setWinner(winner);

        Match updatedMatch =
                matchRepository.save(match);

        return mapToResponse(updatedMatch);
    }

    @Override
    public void deleteMatch(Long id) {

        if (!matchRepository.existsById(id)) {

            throw new ResourceNotFoundException(
                    "Match not found with id: " + id
            );
        }

        matchRepository.deleteById(id);
    }

    // ---------------------------------------------------------
    // Helper methods
    // ---------------------------------------------------------

    private Competition findCompetitionById(
            Long competitionId) {

        return competitionRepository.findById(competitionId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Competition not found with id: "
                                        + competitionId
                        )
                );
    }

    private Season findSeasonById(Long seasonId) {

        return seasonRepository.findById(seasonId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Season not found with id: "
                                        + seasonId
                        )
                );
    }

    private Venue findVenueById(Long venueId) {

        return venueRepository.findById(venueId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Venue not found with id: "
                                        + venueId
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

    private void validateTeams(
            Team team1,
            Team team2) {

        if (team1.getId().equals(team2.getId())) {

            throw new IllegalArgumentException(
                    "Team 1 and Team 2 cannot be the same"
            );
        }
    }

    private void validateTeamParticipates(
            Team selectedTeam,
            Team team1,
            Team team2,
            String fieldName) {

        boolean participates =
                selectedTeam.getId().equals(team1.getId())
                        || selectedTeam.getId().equals(team2.getId());

        if (!participates) {

            throw new IllegalArgumentException(
                    fieldName
                            + " must be one of the participating teams"
            );
        }
    }

    private void validateSeasonBelongsToCompetition(
            Season season,
            Competition competition) {

        if (!season.getCompetition()
                .getId()
                .equals(competition.getId())) {

            throw new IllegalArgumentException(
                    "Season does not belong to the selected competition"
            );
        }
    }

    private MatchResponseDTO mapToResponse(
            Match match) {

        Competition competition =
                match.getCompetition();

        Season season =
                match.getSeason();

        Venue venue =
                match.getVenue();

        Team team1 =
                match.getTeam1();

        Team team2 =
                match.getTeam2();

        Team tossWinner =
                match.getTossWinner();

        Team winner =
                match.getWinner();

        return MatchResponseDTO.builder()

                .id(match.getId())
                .matchDate(match.getMatchDate())
                .matchStatus(match.getMatchStatus())
                .tossDecision(match.getTossDecision())
                .resultDescription(
                        match.getResultDescription()
                )

                // Competition
                .competitionId(
                        competition != null
                                ? competition.getId()
                                : null
                )
                .competitionName(
                        competition != null
                                ? competition.getName()
                                : null
                )
                .competitionFormat(
                        competition != null
                                ? competition.getFormat()
                                : null
                )

                // Season
                .seasonId(
                        season != null
                                ? season.getId()
                                : null
                )
                .seasonName(
                        season != null
                                ? season.getName()
                                : null
                )

                // Venue
                .venueId(
                        venue != null
                                ? venue.getId()
                                : null
                )
                .venueName(
                        venue != null
                                ? venue.getName()
                                : null
                )
                .venueCity(
                        venue != null
                                ? venue.getCity()
                                : null
                )
                .venueCountry(
                        venue != null
                                ? venue.getCountry()
                                : null
                )

                // Team 1
                .team1Id(
                        team1 != null
                                ? team1.getId()
                                : null
                )
                .team1Name(
                        team1 != null
                                ? team1.getName()
                                : null
                )
                .team1ShortName(
                        team1 != null
                                ? team1.getShortName()
                                : null
                )

                // Team 2
                .team2Id(
                        team2 != null
                                ? team2.getId()
                                : null
                )
                .team2Name(
                        team2 != null
                                ? team2.getName()
                                : null
                )
                .team2ShortName(
                        team2 != null
                                ? team2.getShortName()
                                : null
                )

                // Toss winner
                .tossWinnerTeamId(
                        tossWinner != null
                                ? tossWinner.getId()
                                : null
                )
                .tossWinnerTeamName(
                        tossWinner != null
                                ? tossWinner.getName()
                                : null
                )

                // Match winner
                .winnerTeamId(
                        winner != null
                                ? winner.getId()
                                : null
                )
                .winnerTeamName(
                        winner != null
                                ? winner.getName()
                                : null
                )

                .build();
    }
}