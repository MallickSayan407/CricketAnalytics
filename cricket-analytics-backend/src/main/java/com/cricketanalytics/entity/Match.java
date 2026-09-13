package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;

@Entity
@Table(
        name = "matches",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_match_external_id",
                        columnNames = "externalId"
                )
        }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Match {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /**
     * Stable match identifier from Cricsheet.
     * Example: 1000887
     */
    @Column(unique = true)
    private String externalId;

    @Column(nullable = false)
    private LocalDate matchDate;

    @Column(nullable = false)
    private String matchStatus;
    
    @Column(nullable = false)
    @Builder.Default
    private String stage = "League";
    
    @Column(nullable = false)
    @Builder.Default
    private Boolean countedInStandings = true;

    private String tossDecision;

    private String resultDescription;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "competition_id", nullable = false)
    private Competition competition;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "season_id", nullable = false)
    private Season season;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "venue_id", nullable = false)
    private Venue venue;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "team1_id", nullable = false)
    private Team team1;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "team2_id", nullable = false)
    private Team team2;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "toss_winner_team_id")
    private Team tossWinner;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "winner_team_id")
    private Team winner;
}