package com.cricketanalytics.repository;

import com.cricketanalytics.entity.Match;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public interface MatchRepository extends JpaRepository<Match, Long> {

    Optional<Match> findByExternalId(String externalId);

    List<Match> findByCompetition_Id(Long competitionId);

    List<Match> findBySeason_Id(Long seasonId);

    List<Match> findByVenue_Id(Long venueId);

    List<Match> findByTeam1_IdOrTeam2_Id(Long team1Id, Long team2Id);

    List<Match> findByMatchDateBetween(
            LocalDate startDate,
            LocalDate endDate
    );
}