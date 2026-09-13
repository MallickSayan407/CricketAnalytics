package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(
    name = "match_team_stats",
    uniqueConstraints = @UniqueConstraint(
        name = "uk_match_team",
        columnNames = {"match_id", "team_id"}
    )
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class MatchTeamStats {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "match_id", nullable = false)
    private Match match;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "team_id", nullable = false)
    private Team team;

    @Column(nullable = false)
    @Builder.Default
    private Integer runs = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer wickets = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer totalBalls = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer allocatedBalls = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer fours = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer sixes = 0;

    @Column(nullable = false)
    @Builder.Default
    private Integer extras = 0;

    @Column(nullable = false)
    @Builder.Default
    private Double runRate = 0.0;
}