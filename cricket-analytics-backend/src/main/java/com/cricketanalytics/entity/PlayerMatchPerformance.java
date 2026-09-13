package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(
        name = "player_match_performance",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_player_match",
                        columnNames = {
                                "player_id",
                                "match_id"
                        }
                )
        }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PlayerMatchPerformance {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // =========================================================
    // Relationships
    // =========================================================

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "player_id", nullable = false)
    private Player player;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "match_id", nullable = false)
    private Match match;

    /**
     * Team represented by the player in this particular match.
     *
     * This is intentionally separate from Player.team because
     * a player can represent different teams across competitions
     * and IPL seasons.
     *
     * Existing ODI records may initially have this field NULL.
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "team_id")
    private Team team;


    // =========================================================
    // Batting
    // =========================================================

    @Column(nullable = false)
    @Builder.Default
    private Integer battingRuns = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer ballsFaced = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer fours = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer sixes = 0;

    /*
     * Calculated as:
     *
     * battingRuns / ballsFaced × 100
     */
    @Column(nullable = false)
    @Builder.Default
    private Double battingStrikeRate = 0.0;

    @Column(nullable = false)
    @Builder.Default
    private Boolean notOut = false;


    // =========================================================
    // Bowling
    // =========================================================

    /*
     * Bowling workload is stored as total legal deliveries.
     *
     * Examples:
     *
     * 10 overs     = 60 balls
     * 10 overs 1 ball = 61 balls
     * 10 overs 5 balls = 65 balls
     */
    @Column(nullable = false)
    @Builder.Default
    private Integer ballsBowled = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer runsConceded = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer wickets = 0;

    /*
     * Calculated as:
     *
     * runsConceded / overs
     *
     * where overs = ballsBowled / 6
     */
    @Column(nullable = false)
    @Builder.Default
    private Double bowlingEconomy = 0.0;

    @Column(nullable = false)
    @Builder.Default
    private Integer maidens = 0;
}