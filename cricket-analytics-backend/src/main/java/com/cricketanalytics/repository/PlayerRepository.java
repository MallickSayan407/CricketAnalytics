package com.cricketanalytics.repository;

import com.cricketanalytics.entity.Player;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface PlayerRepository extends JpaRepository<Player, Long> {

    List<Player> findByTeam_Id(Long teamId);

    List<Player> findByNameContainingIgnoreCase(String name);
}