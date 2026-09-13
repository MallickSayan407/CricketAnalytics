package com.cricketanalytics.repository;

import com.cricketanalytics.entity.PlayerMatchPerformance;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface PlayerMatchPerformanceRepository
        extends JpaRepository<PlayerMatchPerformance, Long> {

    List<PlayerMatchPerformance> findByPlayer_Id(Long playerId);

    List<PlayerMatchPerformance> findByMatch_Id(Long matchId);

    Optional<PlayerMatchPerformance> findByPlayer_IdAndMatch_Id(
            Long playerId,
            Long matchId
    );

    boolean existsByPlayer_IdAndMatch_Id(
            Long playerId,
            Long matchId
    );
}