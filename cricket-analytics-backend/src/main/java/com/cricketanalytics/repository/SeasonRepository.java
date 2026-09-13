package com.cricketanalytics.repository;

import com.cricketanalytics.entity.Season;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SeasonRepository extends JpaRepository<Season, Long> {

    List<Season> findByCompetition_Id(Long competitionId);

    Optional<Season> findByNameIgnoreCaseAndCompetition_Id(
            String name,
            Long competitionId
    );

    boolean existsByNameIgnoreCaseAndCompetition_Id(
            String name,
            Long competitionId
    );
}