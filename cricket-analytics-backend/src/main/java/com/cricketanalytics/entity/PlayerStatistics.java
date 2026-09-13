package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(
        name = "player_statistics",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_player_competition_season_scope",
                        columnNames = {
                                "player_id",
                                "competition_id",
                                "season_id",
                                "scope"
                        }
                )
        }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PlayerStatistics {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "player_id", nullable = false)
    private Player player;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "competition_id", nullable = false)
    private Competition competition;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "season_id", nullable = false)
    private Season season;

    /**
     * Statistics scope.
     *
     * CAREER = aggregate statistics across the complete dataset.
     * SEASON = statistics for a particular competition season.
     */
    @Column(nullable = false, length = 20)
    @Builder.Default
    private String scope = "SEASON";

    @Column(nullable = false)
    @Builder.Default
    private Integer matches = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer battingInnings = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer runs = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer ballsFaced = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer highestScore = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer notOuts = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer fours = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer sixes = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer fifties = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer centuries = 0;

    @Column(nullable = false)
    @Builder.Default
    private Double battingAverage = 0.0;

    @Column(nullable = false)
    @Builder.Default
    private Double strikeRate = 0.0;

    @Column(nullable = false)
    @Builder.Default
    private Integer bowlingInnings = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer ballsBowled = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer wickets = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer runsConceded = 0;

    @Column(nullable = false)
    @Builder.Default
    private Double economy = 0.0;

    @Column(nullable = false)
    @Builder.Default
    private Double bowlingAverage = 0.0;

    @Column(nullable = false)
    @Builder.Default
    private Integer bestBowlingWickets = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer fiveWicketHauls = 0;
}