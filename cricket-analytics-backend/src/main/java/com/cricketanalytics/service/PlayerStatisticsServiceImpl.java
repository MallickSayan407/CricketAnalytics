package com.cricketanalytics.service;

import com.cricketanalytics.dto.PlayerStatisticsRequestDTO;
import com.cricketanalytics.dto.PlayerStatisticsResponseDTO;
import com.cricketanalytics.entity.Competition;
import com.cricketanalytics.entity.Player;
import com.cricketanalytics.entity.PlayerStatistics;
import com.cricketanalytics.entity.Season;
import com.cricketanalytics.exception.DuplicateResourceException;
import com.cricketanalytics.exception.ResourceNotFoundException;
import com.cricketanalytics.repository.CompetitionRepository;
import com.cricketanalytics.repository.PlayerRepository;
import com.cricketanalytics.repository.PlayerStatisticsRepository;
import com.cricketanalytics.repository.SeasonRepository;

import lombok.RequiredArgsConstructor;

import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class PlayerStatisticsServiceImpl
        implements PlayerStatisticsService {

    private final PlayerStatisticsRepository statisticsRepository;
    private final PlayerRepository playerRepository;
    private final CompetitionRepository competitionRepository;
    private final SeasonRepository seasonRepository;


    // =========================================================
    // CREATE
    // =========================================================

    @Override
    public PlayerStatisticsResponseDTO createStatistics(
            PlayerStatisticsRequestDTO request) {

        Player player = findPlayerById(request.getPlayerId());

        Competition competition =
                findCompetitionById(request.getCompetitionId());

        Season season =
                findSeasonById(request.getSeasonId());

        validateSeasonBelongsToCompetition(
                season,
                competition
        );

        if (statisticsRepository
                .existsByPlayer_IdAndCompetition_IdAndSeason_Id(
                        request.getPlayerId(),
                        request.getCompetitionId(),
                        request.getSeasonId())) {

            throw new DuplicateResourceException(
                    "Statistics already exist for this player, "
                            + "competition and season"
            );
        }

        PlayerStatistics statistics = PlayerStatistics.builder()

                // Relationships
                .player(player)
                .competition(competition)
                .season(season)

                // Batting
                .matches(request.getMatches())
                .battingInnings(request.getBattingInnings())
                .runs(request.getRuns())
                .ballsFaced(request.getBallsFaced())
                .highestScore(request.getHighestScore())
                .notOuts(request.getNotOuts())
                .fours(request.getFours())
                .sixes(request.getSixes())
                .fifties(request.getFifties())
                .centuries(request.getCenturies())

                // Bowling
                .bowlingInnings(request.getBowlingInnings())
                .ballsBowled(request.getBallsBowled())
                .wickets(request.getWickets())
                .runsConceded(request.getRunsConceded())
                .bestBowlingWickets(
                        request.getBestBowlingWickets()
                )
                .fiveWicketHauls(
                        request.getFiveWicketHauls()
                )

                .build();

        calculateDerivedStatistics(statistics);

        PlayerStatistics savedStatistics =
                statisticsRepository.save(statistics);

        return mapToResponse(savedStatistics);
    }


    // =========================================================
    // GET ALL
    // =========================================================

    @Override
    public List<PlayerStatisticsResponseDTO> getAllStatistics() {

        return statisticsRepository.findAll()
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // GET BY ID
    // =========================================================

    @Override
    public PlayerStatisticsResponseDTO getStatisticsById(
            Long id) {

        PlayerStatistics statistics =
                statisticsRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Player statistics not found with id: "
                                                + id
                                )
                        );

        return mapToResponse(statistics);
    }


    // =========================================================
    // GET BY PLAYER + COMPETITION + SEASON
    // =========================================================

    @Override
    public PlayerStatisticsResponseDTO getPlayerStatistics(
            Long playerId,
            Long competitionId,
            Long seasonId) {

        Player player = findPlayerById(playerId);

        Competition competition =
                findCompetitionById(competitionId);

        Season season =
                findSeasonById(seasonId);

        validateSeasonBelongsToCompetition(
                season,
                competition
        );

        PlayerStatistics statistics =
                statisticsRepository
                        .findByPlayer_IdAndCompetition_IdAndSeason_Id(
                                player.getId(),
                                competition.getId(),
                                season.getId()
                        )
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Statistics not found for "
                                                + "playerId="
                                                + playerId
                                                + ", competitionId="
                                                + competitionId
                                                + ", seasonId="
                                                + seasonId
                                )
                        );

        return mapToResponse(statistics);
    }


    // =========================================================
    // GET BY PLAYER
    // =========================================================

    @Override
    public List<PlayerStatisticsResponseDTO> getStatisticsByPlayer(
            Long playerId) {

        findPlayerById(playerId);

        return statisticsRepository
                .findByPlayer_Id(playerId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // GET BY COMPETITION
    // =========================================================

    @Override
    public List<PlayerStatisticsResponseDTO> getStatisticsByCompetition(
            Long competitionId) {

        findCompetitionById(competitionId);

        return statisticsRepository
                .findByCompetition_Id(competitionId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // GET BY SEASON
    // =========================================================

    @Override
    public List<PlayerStatisticsResponseDTO> getStatisticsBySeason(
            Long seasonId) {

        findSeasonById(seasonId);

        return statisticsRepository
                .findBySeason_Id(seasonId)
                .stream()
                .map(this::mapToResponse)
                .toList();
    }


    // =========================================================
    // UPDATE
    // =========================================================

    @Override
    public PlayerStatisticsResponseDTO updateStatistics(
            Long id,
            PlayerStatisticsRequestDTO request) {

        PlayerStatistics statistics =
                statisticsRepository.findById(id)
                        .orElseThrow(() ->
                                new ResourceNotFoundException(
                                        "Player statistics not found with id: "
                                                + id
                                )
                        );

        Player player =
                findPlayerById(request.getPlayerId());

        Competition competition =
                findCompetitionById(
                        request.getCompetitionId()
                );

        Season season =
                findSeasonById(
                        request.getSeasonId()
                );

        validateSeasonBelongsToCompetition(
                season,
                competition
        );

        statisticsRepository
                .findByPlayer_IdAndCompetition_IdAndSeason_Id(
                        request.getPlayerId(),
                        request.getCompetitionId(),
                        request.getSeasonId()
                )
                .ifPresent(existingStatistics -> {

                    if (!existingStatistics
                            .getId()
                            .equals(id)) {

                        throw new DuplicateResourceException(
                                "Statistics already exist for this "
                                        + "player, competition and season"
                        );
                    }
                });


        // Relationships
        statistics.setPlayer(player);
        statistics.setCompetition(competition);
        statistics.setSeason(season);

        // Batting
        statistics.setMatches(request.getMatches());
        statistics.setBattingInnings(
                request.getBattingInnings()
        );
        statistics.setRuns(request.getRuns());
        statistics.setBallsFaced(request.getBallsFaced());
        statistics.setHighestScore(
                request.getHighestScore()
        );
        statistics.setNotOuts(request.getNotOuts());
        statistics.setFours(request.getFours());
        statistics.setSixes(request.getSixes());
        statistics.setFifties(request.getFifties());
        statistics.setCenturies(request.getCenturies());

        // Bowling
        statistics.setBowlingInnings(
                request.getBowlingInnings()
        );
        statistics.setBallsBowled(
                request.getBallsBowled()
        );
        statistics.setWickets(request.getWickets());
        statistics.setRunsConceded(
                request.getRunsConceded()
        );
        statistics.setBestBowlingWickets(
                request.getBestBowlingWickets()
        );
        statistics.setFiveWicketHauls(
                request.getFiveWicketHauls()
        );

        calculateDerivedStatistics(statistics);

        PlayerStatistics updatedStatistics =
                statisticsRepository.save(statistics);

        return mapToResponse(updatedStatistics);
    }


    // =========================================================
    // DELETE
    // =========================================================

    @Override
    public void deleteStatistics(Long id) {

        if (!statisticsRepository.existsById(id)) {

            throw new ResourceNotFoundException(
                    "Player statistics not found with id: "
                            + id
            );
        }

        statisticsRepository.deleteById(id);
    }


    // =========================================================
    // DERIVED STATISTICS
    // =========================================================

    private void calculateDerivedStatistics(
            PlayerStatistics statistics) {

        int runs = safeInt(statistics.getRuns());
        int battingInnings =
                safeInt(statistics.getBattingInnings());
        int notOuts =
                safeInt(statistics.getNotOuts());

        int ballsFaced =
                safeInt(statistics.getBallsFaced());

        int runsConceded =
                safeInt(statistics.getRunsConceded());

        int ballsBowled =
                safeInt(statistics.getBallsBowled());

        int wickets =
                safeInt(statistics.getWickets());


        // ---------------------------------------------------------
        // Batting Average
        // ---------------------------------------------------------

        int dismissals =
                Math.max(battingInnings - notOuts, 0);

        double battingAverage = 0.0;

        if (dismissals > 0) {
            battingAverage =
                    (double) runs / dismissals;
        }

        statistics.setBattingAverage(
                roundToTwoDecimals(battingAverage)
        );


        // ---------------------------------------------------------
        // Strike Rate
        // ---------------------------------------------------------

        double strikeRate = 0.0;

        if (ballsFaced > 0) {
            strikeRate =
                    ((double) runs / ballsFaced) * 100.0;
        }

        statistics.setStrikeRate(
                roundToTwoDecimals(strikeRate)
        );


        // ---------------------------------------------------------
        // Bowling Economy
        //
        // ballsBowled / 6 = overs
        // ---------------------------------------------------------

        double economy = 0.0;

        if (ballsBowled > 0) {

            double overs =
                    (double) ballsBowled / 6.0;

            economy =
                    (double) runsConceded / overs;
        }

        statistics.setEconomy(
                roundToTwoDecimals(economy)
        );


        // ---------------------------------------------------------
        // Bowling Average
        // ---------------------------------------------------------

        double bowlingAverage = 0.0;

        if (wickets > 0) {
            bowlingAverage =
                    (double) runsConceded / wickets;
        }

        statistics.setBowlingAverage(
                roundToTwoDecimals(bowlingAverage)
        );
    }


    // =========================================================
    // HELPER METHODS
    // =========================================================

    private int safeInt(Integer value) {

        return value == null ? 0 : value;
    }


    private double roundToTwoDecimals(double value) {

        return Math.round(value * 100.0) / 100.0;
    }


    private Player findPlayerById(Long playerId) {

        return playerRepository.findById(playerId)
                .orElseThrow(() ->
                        new ResourceNotFoundException(
                                "Player not found with id: "
                                        + playerId
                        )
                );
    }


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


    // =========================================================
    // ENTITY → RESPONSE DTO
    // =========================================================

    private PlayerStatisticsResponseDTO mapToResponse(
            PlayerStatistics statistics) {

        Player player = statistics.getPlayer();
        Competition competition = statistics.getCompetition();
        Season season = statistics.getSeason();

        return PlayerStatisticsResponseDTO.builder()

                .id(statistics.getId())

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

                // -------------------------------------------------
                // Competition
                // -------------------------------------------------

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

                .competitionType(
                        competition != null
                                ? competition.getType()
                                : null
                )

                .competitionFormat(
                        competition != null
                                ? competition.getFormat()
                                : null
                )

                // -------------------------------------------------
                // Season
                // -------------------------------------------------

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

                // -------------------------------------------------
                // Batting
                // -------------------------------------------------

                .matches(statistics.getMatches())

                .battingInnings(
                        statistics.getBattingInnings()
                )

                .runs(statistics.getRuns())

                .ballsFaced(
                        statistics.getBallsFaced()
                )

                .highestScore(
                        statistics.getHighestScore()
                )

                .notOuts(
                        statistics.getNotOuts()
                )

                .fours(
                        statistics.getFours()
                )

                .sixes(
                        statistics.getSixes()
                )

                .fifties(
                        statistics.getFifties()
                )

                .centuries(
                        statistics.getCenturies()
                )

                .battingAverage(
                        statistics.getBattingAverage()
                )

                .strikeRate(
                        statistics.getStrikeRate()
                )

                // -------------------------------------------------
                // Bowling
                // -------------------------------------------------

                .bowlingInnings(
                        statistics.getBowlingInnings()
                )

                .ballsBowled(
                        statistics.getBallsBowled()
                )

                .wickets(
                        statistics.getWickets()
                )

                .runsConceded(
                        statistics.getRunsConceded()
                )

                .economy(
                        statistics.getEconomy()
                )

                .bowlingAverage(
                        statistics.getBowlingAverage()
                )

                .bestBowlingWickets(
                        statistics.getBestBowlingWickets()
                )

                .fiveWicketHauls(
                        statistics.getFiveWicketHauls()
                )

                .build();
    }
}