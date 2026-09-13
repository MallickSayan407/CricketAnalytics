package com.cricketanalytics.repository;

import com.cricketanalytics.entity.Venue;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface VenueRepository extends JpaRepository<Venue, Long> {

    Optional<Venue> findByNameIgnoreCase(String name);

    List<Venue> findByCountryIgnoreCase(String country);

    List<Venue> findByCityIgnoreCase(String city);

    boolean existsByNameIgnoreCase(String name);
}