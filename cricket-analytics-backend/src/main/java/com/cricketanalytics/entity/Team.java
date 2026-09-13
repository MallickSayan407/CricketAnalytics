package com.cricketanalytics.entity;

import jakarta.persistence.*;
import lombok.*;

import java.util.ArrayList;
import java.util.List;

@Entity
@Table(
        name = "teams",
        uniqueConstraints = {
                @UniqueConstraint(
                        name = "uk_team_name_gender",
                        columnNames = {"name", "gender"}
                ),
                @UniqueConstraint(
                        name = "uk_team_short_name_gender",
                        columnNames = {"short_name", "gender"}
                )
        }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Team {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false, length = 10)
    private String shortName;

    @Column(nullable = false)
    private String country;

    @Column(nullable = false, length = 10)
    @Builder.Default
    private String gender = "male";

    private String logoUrl;

    @OneToMany(mappedBy = "team", cascade = CascadeType.ALL)
    @Builder.Default
    private List<Player> players = new ArrayList<>();
}