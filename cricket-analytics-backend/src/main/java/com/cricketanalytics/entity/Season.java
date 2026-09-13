package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(
        name = "seasons",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_season_competition",
                        columnNames = {"name", "competition_id"}
                )
        }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Season {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false)
    private Integer startYear;

    private Integer endYear;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "competition_id", nullable = false)
    private Competition competition;
}