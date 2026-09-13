package com.cricketanalytics.repository;

import com.cricketanalytics.entity.PlayerStatistics;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PlayerStatisticsRepository
        extends JpaRepository<PlayerStatistics, Long> {

    // --------------------------------------------------------
    // Scope-aware methods
    // --------------------------------------------------------

    Optional<PlayerStatistics>
    findByPlayer_IdAndCompetition_IdAndSeason_IdAndScope(
            Long playerId,
            Long competitionId,
            Long seasonId,
            String scope
    );

    boolean existsByPlayer_IdAndCompetition_IdAndSeason_IdAndScope(
            Long playerId,
            Long competitionId,
            Long seasonId,
            String scope
    );

    List<PlayerStatistics> findByPlayer_IdAndScope(
            Long playerId,
            String scope
    );

    List<PlayerStatistics> findByScope(
            String scope
    );

    // --------------------------------------------------------
    // Existing methods used by current application
    // --------------------------------------------------------

    Optional<PlayerStatistics>
    findByPlayer_IdAndCompetition_IdAndSeason_Id(
            Long playerId,
            Long competitionId,
            Long seasonId
    );

    boolean existsByPlayer_IdAndCompetition_IdAndSeason_Id(
            Long playerId,
            Long competitionId,
            Long seasonId
    );

    List<PlayerStatistics> findByPlayer_Id(
            Long playerId
    );

    List<PlayerStatistics> findByCompetition_Id(
            Long competitionId
    );

    List<PlayerStatistics> findBySeason_Id(
            Long seasonId
    );

    List<PlayerStatistics>
    findAllByOrderByRunsDesc();

    List<PlayerStatistics>
    findAllByOrderByBattingAverageDesc();

    List<PlayerStatistics>
    findAllByOrderByStrikeRateDesc();

    List<PlayerStatistics>
    findAllByOrderByCenturiesDesc();

    List<PlayerStatistics>
    findAllByOrderByWicketsDesc();

    List<PlayerStatistics>
    findByCompetition_IdAndSeason_Id(
            Long competitionId,
            Long seasonId
    );
}