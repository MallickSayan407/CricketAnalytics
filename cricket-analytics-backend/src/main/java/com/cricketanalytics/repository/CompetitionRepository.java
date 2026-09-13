package com.cricketanalytics.repository;

import com.cricketanalytics.entity.Competition;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface CompetitionRepository extends JpaRepository<Competition, Long> {

    Optional<Competition> findByNameIgnoreCase(String name);

    boolean existsByNameIgnoreCase(String name);
}