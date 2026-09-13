package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

@Entity
@Table(name = "players")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Player {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(unique = true)
    private String externalId;

    @Column(nullable = false)
    private String role;

    private String battingStyle;

    private String bowlingStyle;

    private String avatarUrl;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "team_id")
    private Team team;
}