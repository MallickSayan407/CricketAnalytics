package com.cricketanalytics.repository;

import com.cricketanalytics.entity.Team;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface TeamRepository extends JpaRepository<Team, Long> {

    Optional<Team> findByNameAndGender(
            String name,
            String gender
    );

    Optional<Team> findByShortNameAndGender(
            String shortName,
            String gender
    );

    boolean existsByNameAndGender(
            String name,
            String gender
    );

    boolean existsByShortNameAndGender(
            String shortName,
            String gender
    );
}