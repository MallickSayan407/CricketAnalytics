package com.cricketanalytics.repository;

import com.cricketanalytics.entity.MatchTeamStats;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface MatchTeamStatsRepository
        extends JpaRepository<MatchTeamStats, Long> {

    List<MatchTeamStats> findByMatch_Id(Long matchId);

    List<MatchTeamStats> findByTeam_Id(Long teamId);

    Optional<MatchTeamStats> findByMatch_IdAndTeam_Id(
            Long matchId,
            Long teamId
    );

    boolean existsByMatch_IdAndTeam_Id(
            Long matchId,
            Long teamId
    );
}