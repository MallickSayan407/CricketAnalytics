import csv
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ZIP_PATH = (
    BASE_DIR
    / "raw"
    / "international"
    / "odis_json.zip"
)

OUTPUT_DIR = (
    BASE_DIR
    / "processed"
    / "odi"
)


# =============================================================================
# CRICKET RULES
# =============================================================================

TEAM_WICKET_TYPES = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "run out",
    "stumped",
    "hit wicket",
    "obstructing the field",
    "timed out",
}

BOWLER_WICKET_TYPES = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
}

ILLEGAL_DELIVERY_EXTRAS = {
    "wides",
    "noballs",
}


# =============================================================================
# CSV FIELDS
# =============================================================================

MATCH_FIELDS = [
    "match_id",
    "match_date",
    "gender",
    "match_type",
    "team1",
    "team2",
    "venue",
    "city",
    "country",
    "toss_winner",
    "toss_decision",
    "winner",
    "result_type",
    "result_description",
    "result_method",
    "eliminator",
    "overs",
]


TEAM_FIELDS = [
    "team_id",
    "team_name",
    "gender",
]


MATCH_TEAM_FIELDS = [
    "match_id",
    "team_id",
    "team_name",
    "gender",
    "runs",
    "wickets",
    "total_balls",
    "fours",
    "sixes",
    "extras",
    "run_rate",
]


PLAYER_FIELDS = [
    "player_id",
    "player_external_id",
    "player_name",
    "gender",
    "role",
    "batting_style",
    "bowling_style",
    "team_name",
]


PLAYER_MATCH_FIELDS = [
    "match_id",
    "player_id",
    "player_external_id",
    "player_name",
    "team_id",
    "team_name",
    "gender",
    "batting_runs",
    "balls_faced",
    "fours",
    "sixes",
    "batting_strike_rate",
    "not_out",
    "batted",
    "balls_bowled",
    "runs_conceded",
    "wickets",
    "bowling_economy",
    "maidens",
]


PLAYER_STAT_FIELDS = [
    "player_id",
    "player_external_id",
    "player_name",
    "gender",
    "team_name",
    "matches",
    "batting_innings",
    "runs",
    "balls_faced",
    "highest_score",
    "not_outs",
    "fours",
    "sixes",
    "fifties",
    "centuries",
    "batting_average",
    "strike_rate",
    "bowling_innings",
    "balls_bowled",
    "wickets",
    "runs_conceded",
    "economy",
    "bowling_average",
    "best_bowling_wickets",
    "five_wicket_hauls",
]


# =============================================================================
# GENERAL HELPERS
# =============================================================================

def safe_int(
    value: Any,
    default: int = 0
) -> int:

    try:

        if value is None:
            return default

        return int(value)

    except (TypeError, ValueError):

        return default


def safe_float(
    value: Any,
    default: float = 0.0
) -> float:

    try:

        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):

        return default


def round_value(
    value: float,
    digits: int = 2
) -> float:

    result = round(
        value,
        digits
    )

    if result == -0.0:

        return 0.0

    return result


def get_match_id(
    filename: str
) -> str:

    return Path(
        filename
    ).stem


def get_match_date(
    info: dict
) -> str:

    dates = info.get(
        "dates",
        []
    )

    if not dates:

        return ""

    return str(
        dates[0]
    )


# =============================================================================
# DELIVERY HELPERS
# =============================================================================

def is_legal_delivery(
    delivery: dict
) -> bool:

    extras = delivery.get(
        "extras",
        {}
    )

    return not any(
        extra_type in extras
        for extra_type in ILLEGAL_DELIVERY_EXTRAS
    )


def batter_faces_delivery(
    delivery: dict
) -> bool:

    extras = delivery.get(
        "extras",
        {}
    )

    return (
        "wides" not in extras
        and "noballs" not in extras
    )


def get_runs(
    delivery: dict
) -> dict:

    runs = delivery.get(
        "runs",
        {}
    )

    return {
        "batter": safe_int(
            runs.get("batter")
        ),
        "extras": safe_int(
            runs.get("extras")
        ),
        "total": safe_int(
            runs.get("total")
        ),
    }


def get_extra_runs(
    delivery: dict
) -> dict:

    extras = delivery.get(
        "extras",
        {}
    )

    return {
        "wides": safe_int(
            extras.get("wides")
        ),
        "noballs": safe_int(
            extras.get("noballs")
        ),
        "byes": safe_int(
            extras.get("byes")
        ),
        "legbyes": safe_int(
            extras.get("legbyes")
        ),
        "penalty": safe_int(
            extras.get("penalty")
        ),
    }


def get_bowler_runs_conceded(
    delivery: dict
) -> int:

    runs = get_runs(
        delivery
    )

    extras = get_extra_runs(
        delivery
    )

    non_bowler_runs = (
        extras["byes"]
        + extras["legbyes"]
    )

    return max(
        0,
        runs["total"] - non_bowler_runs
    )


def get_bowler_wickets(
    delivery: dict
) -> int:

    wickets = delivery.get(
        "wickets",
        []
    )

    count = 0

    for wicket in wickets:

        wicket_type = str(
            wicket.get(
                "kind",
                ""
            )
        ).lower().strip()

        if wicket_type in BOWLER_WICKET_TYPES:

            count += 1

    return count


def get_team_wickets(
    delivery: dict
) -> int:

    wickets = delivery.get(
        "wickets",
        []
    )

    count = 0

    for wicket in wickets:

        wicket_type = str(
            wicket.get(
                "kind",
                ""
            )
        ).lower().strip()

        if wicket_type in TEAM_WICKET_TYPES:

            count += 1

    return count


# =============================================================================
# CALCULATIONS
# =============================================================================

def calculate_strike_rate(
    runs: int,
    balls: int
) -> float:

    if balls <= 0:

        return 0.0

    return round_value(
        (runs / balls) * 100
    )


def calculate_batting_average(
    runs: int,
    innings: int,
    not_outs: int
) -> float:

    dismissals = (
        innings - not_outs
    )

    if dismissals <= 0:

        return 0.0

    return round_value(
        runs / dismissals
    )


def calculate_economy(
    runs_conceded: int,
    balls_bowled: int
) -> float:

    if balls_bowled <= 0:

        return 0.0

    return round_value(
        (runs_conceded * 6)
        / balls_bowled
    )


def calculate_bowling_average(
    runs_conceded: int,
    wickets: int
) -> float:

    if wickets <= 0:

        return 0.0

    return round_value(
        runs_conceded / wickets
    )


def calculate_run_rate(
    runs: int,
    legal_balls: int
) -> float:

    if legal_balls <= 0:

        return 0.0

    return round_value(
        (runs * 6)
        / legal_balls
    )


# =============================================================================
# CRICSHEET REGISTRY
# =============================================================================

def get_registry_people(
    info: dict
) -> dict:

    registry = info.get(
        "registry",
        {}
    )

    people = registry.get(
        "people",
        {}
    )

    if not isinstance(
        people,
        dict
    ):

        return {}

    return people


# =============================================================================
# OFFICIAL PLAYER → TEAM MAP
# =============================================================================

def get_player_team_map(
    info: dict
) -> dict:

    result = {}

    players_by_team = info.get(
        "players",
        {}
    )

    if not isinstance(
        players_by_team,
        dict
    ):

        return result

    for team_name, players in (
        players_by_team.items()
    ):

        if not isinstance(
            players,
            list
        ):

            continue

        for player_name in players:

            result[
                player_name
            ] = team_name

    return result


# =============================================================================
# PLAYER IDENTITY
# =============================================================================

def get_player_identity_key(
    player_name: str,
    gender: str,
    external_id: str
) -> tuple:

    """
    Prefer the stable Cricsheet ID.

    If a Cricsheet ID is unavailable, fall back to
    gender + normalized player name.
    """

    if external_id:

        return (
            "external",
            external_id
        )

    return (
        "fallback",
        gender,
        player_name.lower().strip()
    )


# =============================================================================
# REGISTER PLAYER
# =============================================================================

def register_player_identity(
    state: dict,
    identity_key: tuple,
    player_name: str,
    gender: str,
    external_id: str
) -> None:

    existing = state[
        "player_identity"
    ].get(
        identity_key
    )

    if existing is None:

        state[
            "player_identity"
        ][identity_key] = {
            "player_name": player_name,
            "gender": gender,
            "external_id": external_id,
        }

        return

    # External ID is authoritative.
    if external_id:

        existing[
            "external_id"
        ] = external_id


# =============================================================================
# PROCESS MATCH
# =============================================================================

def process_match(
    match_id: str,
    data: dict,
    state: dict
) -> None:

    info = data.get(
        "info",
        {}
    )

    teams = info.get(
        "teams",
        []
    )

    if len(teams) < 2:

        return

    gender = str(
        info.get(
            "gender",
            ""
        )
    ).lower()

    match_type = str(
        info.get(
            "match_type",
            ""
        )
    )

    match_date = get_match_date(
        info
    )

    venue = info.get(
        "venue",
        ""
    )

    city = info.get(
        "city",
        ""
    )

    registry_people = get_registry_people(
        info
    )

    official_player_teams = (
        get_player_team_map(
            info
        )
    )

    # =========================================================================
    # TOSS
    # =========================================================================

    toss = info.get(
        "toss",
        {}
    )

    toss_winner = toss.get(
        "winner",
        ""
    )

    toss_decision = toss.get(
        "decision",
        ""
    )

    # =========================================================================
    # OUTCOME
    # =========================================================================

    outcome = info.get(
        "outcome",
        {}
    )

    winner = ""
    result_type = ""
    result_description = ""

    result_method = outcome.get(
        "method",
        ""
    )

    eliminator = outcome.get(
        "eliminator",
        ""
    )

    if "winner" in outcome:

        winner = outcome.get(
            "winner",
            ""
        )

        result_type = "winner"

        outcome_by = outcome.get(
            "by",
            {}
        )

        if "runs" in outcome_by:

            result_description = (
                f"{winner} won by "
                f"{safe_int(outcome_by['runs'])} runs"
            )

        elif "wickets" in outcome_by:

            result_description = (
                f"{winner} won by "
                f"{safe_int(outcome_by['wickets'])} wickets"
            )

        elif "innings" in outcome_by:

            result_description = (
                f"{winner} won by "
                f"{safe_int(outcome_by['innings'])} innings"
            )

        else:

            result_description = (
                f"{winner} won"
            )

    elif outcome.get(
        "result"
    ) == "tie":

        result_type = "tie"

        result_description = (
            "Match tied"
        )

    elif outcome.get(
        "result"
    ) in {
        "no result",
        "no_result",
    }:

        result_type = "no_result"

        result_description = (
            "No result"
        )

    elif outcome.get(
        "result"
    ):

        result_type = str(
            outcome.get(
                "result"
            )
        )

        result_description = (
            result_type
        )

    # =========================================================================
    # MATCH ROW
    # =========================================================================

    state[
        "matches"
    ].append(
        {
            "match_id": match_id,
            "match_date": match_date,
            "gender": gender,
            "match_type": match_type,
            "team1": teams[0],
            "team2": teams[1],
            "venue": venue,
            "city": city,
            "country": "",
            "toss_winner": toss_winner,
            "toss_decision": toss_decision,
            "winner": winner,
            "result_type": result_type,
            "result_description": result_description,
            "result_method": result_method,
            "eliminator": eliminator,
            "overs": safe_int(
                info.get(
                    "overs"
                )
            ),
        }
    )

    # =========================================================================
    # TEAM IDS
    # =========================================================================

    for team_name in teams:

        team_key = (
            gender,
            team_name
        )

        if team_key not in state[
            "team_map"
        ]:

            team_id = (
                len(
                    state["team_map"]
                ) + 1
            )

            state[
                "team_map"
            ][team_key] = team_id

            state[
                "teams"
            ].append(
                {
                    "team_id": team_id,
                    "team_name": team_name,
                    "gender": gender,
                }
            )

    # =========================================================================
    # ONE PLAYER RECORD PER MATCH
    # =========================================================================

    match_players = {}

    def get_match_player(
        player_name: str
    ) -> dict:

        external_id = registry_people.get(
            player_name,
            ""
        )

        identity_key = get_player_identity_key(
            player_name,
            gender,
            external_id
        )

        if identity_key not in match_players:

            actual_team = (
                official_player_teams.get(
                    player_name
                )
            )

            match_players[
                identity_key
            ] = {
                "identity_key": identity_key,
                "player_name": player_name,
                "external_id": external_id,
                "gender": gender,
                "team_name": actual_team or "",
                "batting_runs": 0,
                "balls_faced": 0,
                "fours": 0,
                "sixes": 0,
                "batted": False,
                "dismissed": False,
                "balls_bowled": 0,
                "runs_conceded": 0,
                "wickets": 0,
                "maidens": 0,
            }

        else:

            record = match_players[
                identity_key
            ]

            if (
                not record["external_id"]
                and external_id
            ):

                record[
                    "external_id"
                ] = external_id

            if (
                not record["team_name"]
                and player_name in official_player_teams
            ):

                record[
                    "team_name"
                ] = official_player_teams[
                    player_name
                ]

        return match_players[
            identity_key
        ]

    # =========================================================================
    # PROCESS NORMAL INNINGS
    # =========================================================================

    for innings_data in data.get(
        "innings",
        []
    ):

        # ---------------------------------------------------------------------
        # Super overs / eliminator innings are not normal ODI innings.
        # ---------------------------------------------------------------------

        if innings_data.get(
            "super_over",
            False
        ):

            continue

        batting_team = innings_data.get(
            "team",
            ""
        )

        if not batting_team:

            continue

        batting_team_id = state[
            "team_map"
        ].get(
            (
                gender,
                batting_team
            )
        )

        if batting_team_id is None:

            continue

        # =========================================================================
        # TEAM TOTALS
        # =========================================================================

        team_runs = 0
        team_wickets = 0
        legal_balls = 0
        team_fours = 0
        team_sixes = 0
        team_extras = 0

        # =========================================================================
        # PROCESS OVERS
        # =========================================================================

        for over_data in innings_data.get(
            "overs",
            []
        ):

            deliveries = over_data.get(
                "deliveries",
                []
            )

            over_bowler_runs = defaultdict(
                int
            )

            over_bowler_legal_balls = defaultdict(
                int
            )

            for delivery in deliveries:

                batter_name = delivery.get(
                    "batter",
                    ""
                )

                bowler_name = delivery.get(
                    "bowler",
                    ""
                )

                # -------------------------------------------------------------
                # REGISTER BATTER
                # -------------------------------------------------------------

                if batter_name:

                    batter_record = get_match_player(
                        batter_name
                    )

                    batter_record[
                        "batted"
                    ] = True

                # -------------------------------------------------------------
                # REGISTER BOWLER
                # -------------------------------------------------------------

                if bowler_name:

                    get_match_player(
                        bowler_name
                    )

                # -------------------------------------------------------------
                # RUNS
                # -------------------------------------------------------------

                runs = get_runs(
                    delivery
                )

                team_runs += runs[
                    "total"
                ]

                team_extras += runs[
                    "extras"
                ]

                if runs[
                    "batter"
                ] == 4:

                    team_fours += 1

                if runs[
                    "batter"
                ] == 6:

                    team_sixes += 1

                # -------------------------------------------------------------
                # WICKETS
                # -------------------------------------------------------------

                team_wickets += get_team_wickets(
                    delivery
                )

                # -------------------------------------------------------------
                # LEGAL BALL
                # -------------------------------------------------------------

                legal = is_legal_delivery(
                    delivery
                )

                if legal:

                    legal_balls += 1

                # -------------------------------------------------------------
                # BATTING
                # -------------------------------------------------------------

                if batter_name:

                    batter_record = get_match_player(
                        batter_name
                    )

                    batter_record[
                        "batting_runs"
                    ] += runs[
                        "batter"
                    ]

                    if batter_faces_delivery(
                        delivery
                    ):

                        batter_record[
                            "balls_faced"
                        ] += 1

                    if runs[
                        "batter"
                    ] == 4:

                        batter_record[
                            "fours"
                        ] += 1

                    if runs[
                        "batter"
                    ] == 6:

                        batter_record[
                            "sixes"
                        ] += 1

                # -------------------------------------------------------------
                # BOWLING
                # -------------------------------------------------------------

                if bowler_name:

                    bowler_record = get_match_player(
                        bowler_name
                    )

                    bowler_runs = (
                        get_bowler_runs_conceded(
                            delivery
                        )
                    )

                    bowler_wickets = (
                        get_bowler_wickets(
                            delivery
                        )
                    )

                    bowler_record[
                        "runs_conceded"
                    ] += bowler_runs

                    bowler_record[
                        "wickets"
                    ] += bowler_wickets

                    if legal:

                        bowler_record[
                            "balls_bowled"
                        ] += 1

                    over_bowler_runs[
                        bowler_name
                    ] += bowler_runs

                    if legal:

                        over_bowler_legal_balls[
                            bowler_name
                        ] += 1

            # =================================================================
            # MAIDEN OVER
            # =================================================================

            for bowler_name, balls in (
                over_bowler_legal_balls.items()
            ):

                if (
                    balls >= 6
                    and over_bowler_runs[
                        bowler_name
                    ] == 0
                ):

                    bowler_record = get_match_player(
                        bowler_name
                    )

                    bowler_record[
                        "maidens"
                    ] += 1

        # =========================================================================
        # MATCH TEAM STATISTICS
        # =========================================================================

        state[
            "match_team_stats"
        ].append(
            {
                "match_id": match_id,
                "team_id": batting_team_id,
                "team_name": batting_team,
                "gender": gender,
                "runs": team_runs,
                "wickets": team_wickets,
                "total_balls": legal_balls,
                "fours": team_fours,
                "sixes": team_sixes,
                "extras": team_extras,
                "run_rate": calculate_run_rate(
                    team_runs,
                    legal_balls
                ),
            }
        )

    # =========================================================================
    # DETERMINE DISMISSED BATTERS
    # =========================================================================

    for innings_data in data.get(
        "innings",
        []
    ):

        if innings_data.get(
            "super_over",
            False
        ):

            continue

        for over_data in innings_data.get(
            "overs",
            []
        ):

            for delivery in over_data.get(
                "deliveries",
                []
            ):

                for wicket in delivery.get(
                    "wickets",
                    []
                ):

                    wicket_type = str(
                        wicket.get(
                            "kind",
                            ""
                        )
                    ).lower().strip()

                    if wicket_type not in TEAM_WICKET_TYPES:

                        continue

                    player_out = wicket.get(
                        "player_out",
                        ""
                    )

                    if not player_out:

                        continue

                    external_id = registry_people.get(
                        player_out,
                        ""
                    )

                    identity_key = get_player_identity_key(
                        player_out,
                        gender,
                        external_id
                    )

                    if identity_key in match_players:

                        match_players[
                            identity_key
                        ][
                            "dismissed"
                        ] = True

    # =========================================================================
    # BUILD PLAYER MATCH RECORDS
    # =========================================================================

    for identity_key, record in (
        match_players.items()
    ):

        # Only players who actually batted or bowled.
        if (
            not record["batted"]
            and record["balls_bowled"] <= 0
        ):

            continue

        team_name = record[
            "team_name"
        ]

        team_id = None

        if team_name:

            team_id = state[
                "team_map"
            ].get(
                (
                    gender,
                    team_name
                )
            )

        state[
            "player_match_performances"
        ].append(
            {
                "match_id": match_id,
                "player_id": None,
                "player_external_id": record[
                    "external_id"
                ],
                "player_name": record[
                    "player_name"
                ],
                "team_id": team_id,
                "team_name": team_name,
                "gender": gender,
                "batting_runs": record[
                    "batting_runs"
                ],
                "balls_faced": record[
                    "balls_faced"
                ],
                "fours": record[
                    "fours"
                ],
                "sixes": record[
                    "sixes"
                ],
                "batting_strike_rate": calculate_strike_rate(
                    record["batting_runs"],
                    record["balls_faced"]
                ),
                "not_out": (
                    record["batted"]
                    and not record["dismissed"]
                ),
                "batted": record[
                    "batted"
                ],
                "balls_bowled": record[
                    "balls_bowled"
                ],
                "runs_conceded": record[
                    "runs_conceded"
                ],
                "wickets": record[
                    "wickets"
                ],
                "bowling_economy": calculate_economy(
                    record["runs_conceded"],
                    record["balls_bowled"]
                ),
                "maidens": record[
                    "maidens"
                ],
            }
        )

        # ---------------------------------------------------------------------
        # PLAYER IDENTITY
        # ---------------------------------------------------------------------

        register_player_identity(
            state,
            identity_key,
            record["player_name"],
            gender,
            record["external_id"]
        )

        # ---------------------------------------------------------------------
        # TEAM HISTORY
        # ---------------------------------------------------------------------

        if team_name:

            state[
                "player_teams"
            ][identity_key][
                team_name
            ] += 1


# =============================================================================
# ASSIGN INTERNAL PLAYER IDS
# =============================================================================

def assign_player_ids(
    state: dict
) -> None:

    keys = sorted(
        state[
            "player_identity"
        ].keys(),
        key=lambda key: (
            state[
                "player_identity"
            ][key]["gender"],
            state[
                "player_identity"
            ][key]["player_name"].lower()
        )
    )

    for index, identity_key in enumerate(
        keys,
        start=1
    ):

        state[
            "player_id_map"
        ][identity_key] = index


# =============================================================================
# ASSIGN PLAYER IDS TO MATCH RECORDS
# =============================================================================

def update_player_match_ids(
    state: dict
) -> None:

    for record in state[
        "player_match_performances"
    ]:

        identity_key = get_player_identity_key(
            record["player_name"],
            record["gender"],
            record["player_external_id"]
        )

        record[
            "player_id"
        ] = state[
            "player_id_map"
        ].get(
            identity_key
        )


# =============================================================================
# AGGREGATE PLAYER STATISTICS
# =============================================================================

def aggregate_player_statistics(
    state: dict
) -> list:

    grouped = defaultdict(
        lambda: {
            "matches": set(),
            "batting_innings": 0,
            "runs": 0,
            "balls_faced": 0,
            "highest_score": 0,
            "not_outs": 0,
            "fours": 0,
            "sixes": 0,
            "fifties": 0,
            "centuries": 0,
            "bowling_innings": 0,
            "balls_bowled": 0,
            "wickets": 0,
            "runs_conceded": 0,
            "best_bowling_wickets": 0,
            "five_wicket_hauls": 0,
        }
    )

    for record in state[
        "player_match_performances"
    ]:

        identity_key = get_player_identity_key(
            record["player_name"],
            record["gender"],
            record["player_external_id"]
        )

        stats = grouped[
            identity_key
        ]

        stats[
            "matches"
        ].add(
            record["match_id"]
        )

        # =====================================================================
        # BATTING
        # =====================================================================

        if record[
            "batted"
        ]:

            stats[
                "batting_innings"
            ] += 1

            runs = safe_int(
                record["batting_runs"]
            )

            stats[
                "runs"
            ] += runs

            stats[
                "balls_faced"
            ] += safe_int(
                record["balls_faced"]
            )

            stats[
                "fours"
            ] += safe_int(
                record["fours"]
            )

            stats[
                "sixes"
            ] += safe_int(
                record["sixes"]
            )

            stats[
                "highest_score"
            ] = max(
                stats["highest_score"],
                runs
            )

            if record[
                "not_out"
            ]:

                stats[
                    "not_outs"
                ] += 1

            if runs >= 100:

                stats[
                    "centuries"
                ] += 1

            elif runs >= 50:

                stats[
                    "fifties"
                ] += 1

        # =====================================================================
        # BOWLING
        # =====================================================================

        balls_bowled = safe_int(
            record["balls_bowled"]
        )

        wickets = safe_int(
            record["wickets"]
        )

        runs_conceded = safe_int(
            record["runs_conceded"]
        )

        if balls_bowled > 0:

            stats[
                "bowling_innings"
            ] += 1

            stats[
                "balls_bowled"
            ] += balls_bowled

            stats[
                "wickets"
            ] += wickets

            stats[
                "runs_conceded"
            ] += runs_conceded

            stats[
                "best_bowling_wickets"
            ] = max(
                stats["best_bowling_wickets"],
                wickets
            )

            if wickets >= 5:

                stats[
                    "five_wicket_hauls"
                ] += 1

    # =========================================================================
    # BUILD ROWS
    # =========================================================================

    rows = []

    sorted_items = sorted(
        grouped.items(),
        key=lambda item: (
            state[
                "player_identity"
            ][item[0]]["gender"],
            state[
                "player_identity"
            ][item[0]]["player_name"].lower()
        )
    )

    for identity_key, stats in sorted_items:

        identity = state[
            "player_identity"
        ][identity_key]

        team_counter = state[
            "player_teams"
        ].get(
            identity_key,
            Counter()
        )

        team_name = ""

        if team_counter:

            team_name = (
                team_counter.most_common(
                    1
                )[0][0]
            )

        rows.append(
            {
                "player_id": state[
                    "player_id_map"
                ][identity_key],

                "player_external_id": identity[
                    "external_id"
                ],

                "player_name": identity[
                    "player_name"
                ],

                "gender": identity[
                    "gender"
                ],

                "team_name": team_name,

                "matches": len(
                    stats["matches"]
                ),

                "batting_innings": stats[
                    "batting_innings"
                ],

                "runs": stats[
                    "runs"
                ],

                "balls_faced": stats[
                    "balls_faced"
                ],

                "highest_score": stats[
                    "highest_score"
                ],

                "not_outs": stats[
                    "not_outs"
                ],

                "fours": stats[
                    "fours"
                ],

                "sixes": stats[
                    "sixes"
                ],

                "fifties": stats[
                    "fifties"
                ],

                "centuries": stats[
                    "centuries"
                ],

                "batting_average": calculate_batting_average(
                    stats["runs"],
                    stats["batting_innings"],
                    stats["not_outs"]
                ),

                "strike_rate": calculate_strike_rate(
                    stats["runs"],
                    stats["balls_faced"]
                ),

                "bowling_innings": stats[
                    "bowling_innings"
                ],

                "balls_bowled": stats[
                    "balls_bowled"
                ],

                "wickets": stats[
                    "wickets"
                ],

                "runs_conceded": stats[
                    "runs_conceded"
                ],

                "economy": calculate_economy(
                    stats["runs_conceded"],
                    stats["balls_bowled"]
                ),

                "bowling_average": calculate_bowling_average(
                    stats["runs_conceded"],
                    stats["wickets"]
                ),

                "best_bowling_wickets": stats[
                    "best_bowling_wickets"
                ],

                "five_wicket_hauls": stats[
                    "five_wicket_hauls"
                ],
            }
        )

    return rows


# =============================================================================
# DETERMINE PLAYER ROLE
# =============================================================================

def determine_role(
    state: dict,
    identity_key: tuple
) -> str:

    has_batting = False
    has_bowling = False

    for record in state[
        "player_match_performances"
    ]:

        record_key = get_player_identity_key(
            record["player_name"],
            record["gender"],
            record["player_external_id"]
        )

        if record_key != identity_key:

            continue

        if record[
            "batted"
        ]:

            has_batting = True

        if record[
            "balls_bowled"
        ] > 0:

            has_bowling = True

        if has_batting and has_bowling:

            return "ALL_ROUNDER"

    if has_batting:

        return "BATTER"

    if has_bowling:

        return "BOWLER"

    return "UNKNOWN"


# =============================================================================
# BUILD PLAYERS
# =============================================================================

def build_players(
    state: dict
) -> list:

    rows = []

    sorted_keys = sorted(
        state[
            "player_identity"
        ].keys(),
        key=lambda key: (
            state[
                "player_identity"
            ][key]["gender"],
            state[
                "player_identity"
            ][key]["player_name"].lower()
        )
    )

    for identity_key in sorted_keys:

        identity = state[
            "player_identity"
        ][identity_key]

        team_counter = state[
            "player_teams"
        ].get(
            identity_key,
            Counter()
        )

        team_name = ""

        if team_counter:

            team_name = (
                team_counter.most_common(
                    1
                )[0][0]
            )

        rows.append(
            {
                "player_id": state[
                    "player_id_map"
                ][identity_key],

                "player_external_id": identity[
                    "external_id"
                ],

                "player_name": identity[
                    "player_name"
                ],

                "gender": identity[
                    "gender"
                ],

                "role": determine_role(
                    state,
                    identity_key
                ),

                "batting_style": "",

                "bowling_style": "",

                "team_name": team_name,
            }
        )

    return rows


# =============================================================================
# WRITE CSV
# =============================================================================

def write_csv(
    filepath: Path,
    fieldnames: list,
    rows: list
) -> None:

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with filepath.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore"
        )

        writer.writeheader()

        writer.writerows(
            rows
        )


# =============================================================================
# FILE SIZE
# =============================================================================

def format_file_size(
    filepath: Path
) -> str:

    size = filepath.stat().st_size

    if size < 1024:

        return f"{size} B"

    if size < 1024 * 1024:

        return f"{size / 1024:.2f} KB"

    if size < 1024 * 1024 * 1024:

        return (
            f"{size / (1024 * 1024):.2f} MB"
        )

    return (
        f"{size / (1024 * 1024 * 1024):.2f} GB"
    )


# =============================================================================
# MAIN
# =============================================================================

def run_import() -> None:

    print("=" * 80)
    print("CRICSHEET ODI IMPORTER")
    print("=" * 80)

    print()
    print("Source:")
    print(ZIP_PATH)

    print()
    print("Output:")
    print(OUTPUT_DIR)

    if not ZIP_PATH.exists():

        raise FileNotFoundError(
            f"ODI ZIP not found: {ZIP_PATH}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # =========================================================================
    # STATE
    # =========================================================================

    state = {
        "matches": [],
        "teams": [],
        "match_team_stats": [],
        "player_match_performances": [],
        "player_statistics": [],
        "players": [],

        "team_map": {},

        "player_identity": {},

        "player_id_map": {},

        "player_teams": defaultdict(
            Counter
        ),
    }

    processed_matches = 0
    failed_matches = 0

    men_matches = 0
    women_matches = 0

    completed_matches = 0
    tied_matches = 0
    no_result_matches = 0

    total_deliveries = 0

    # =========================================================================
    # READ ARCHIVE
    # =========================================================================

    print()
    print("Reading archive...")

    with zipfile.ZipFile(
        ZIP_PATH,
        "r"
    ) as archive:

        json_files = [
            filename
            for filename in archive.namelist()
            if filename.lower().endswith(
                ".json"
            )
        ]

        json_files.sort()

        total_files = len(
            json_files
        )

        for index, filename in enumerate(
            json_files,
            start=1
        ):

            try:

                with archive.open(
                    filename
                ) as file:

                    data = json.load(
                        file
                    )

                info = data.get(
                    "info",
                    {}
                )

                gender = str(
                    info.get(
                        "gender",
                        ""
                    )
                ).lower()

                if gender == "male":

                    men_matches += 1

                elif gender == "female":

                    women_matches += 1

                outcome = info.get(
                    "outcome",
                    {}
                )

                if "winner" in outcome:

                    completed_matches += 1

                elif outcome.get(
                    "result"
                ) == "tie":

                    tied_matches += 1

                elif outcome.get(
                    "result"
                ) in {
                    "no result",
                    "no_result",
                }:

                    no_result_matches += 1

                # -------------------------------------------------------------
                # SOURCE DELIVERY COUNT
                # -------------------------------------------------------------

                for innings_data in data.get(
                    "innings",
                    []
                ):

                    for over_data in innings_data.get(
                        "overs",
                        []
                    ):

                        total_deliveries += len(
                            over_data.get(
                                "deliveries",
                                []
                            )
                        )

                # -------------------------------------------------------------
                # PROCESS MATCH
                # -------------------------------------------------------------

                process_match(
                    get_match_id(filename),
                    data,
                    state
                )

                processed_matches += 1

            except Exception as exc:

                failed_matches += 1

                print()
                print(
                    f"ERROR: {filename}"
                )

                print(
                    f"       {exc}"
                )

            if index % 250 == 0:

                print(
                    f"Processed "
                    f"{index}/{total_files} matches..."
                )

    # =========================================================================
    # PLAYER IDS
    # =========================================================================

    print()
    print(
        "Assigning stable player identities..."
    )

    assign_player_ids(
        state
    )

    update_player_match_ids(
        state
    )

    # =========================================================================
    # PLAYER STATISTICS
    # =========================================================================

    print(
        "Building player statistics..."
    )

    state[
        "player_statistics"
    ] = aggregate_player_statistics(
        state
    )

    # =========================================================================
    # PLAYERS
    # =========================================================================

    state[
        "players"
    ] = build_players(
        state
    )

    # =========================================================================
    # TOTAL TEAM RUNS
    # =========================================================================

    total_team_runs = sum(
        safe_int(
            row["runs"]
        )
        for row in state[
            "match_team_stats"
        ]
    )

    # =========================================================================
    # WRITE CSV FILES
    # =========================================================================

    print()
    print(
        "Writing CSV files..."
    )

    output_files = {
        "matches.csv": (
            MATCH_FIELDS,
            state["matches"]
        ),

        "teams.csv": (
            TEAM_FIELDS,
            state["teams"]
        ),

        "match_team_stats.csv": (
            MATCH_TEAM_FIELDS,
            state["match_team_stats"]
        ),

        "players.csv": (
            PLAYER_FIELDS,
            state["players"]
        ),

        "player_match_performance.csv": (
            PLAYER_MATCH_FIELDS,
            state["player_match_performances"]
        ),

        "player_statistics.csv": (
            PLAYER_STAT_FIELDS,
            state["player_statistics"]
        ),
    }

    for filename, (
        fields,
        rows
    ) in output_files.items():

        write_csv(
            OUTPUT_DIR / filename,
            fields,
            rows
        )

    # =========================================================================
    # MISSING REGISTRY IDs
    # =========================================================================

    missing_registry_ids = sum(
        1
        for identity in state[
            "player_identity"
        ].values()
        if not identity[
            "external_id"
        ]
    )

    # =========================================================================
    # REPORT
    # =========================================================================

    print()
    print("=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)

    print()
    print(
        f"Archive files:       {total_files}"
    )

    print(
        f"Processed matches:   {processed_matches}"
    )

    print(
        f"Failed matches:      {failed_matches}"
    )

    print(
        f"Men's matches:       {men_matches}"
    )

    print(
        f"Women's matches:     {women_matches}"
    )

    print(
        f"Completed matches:   {completed_matches}"
    )

    print(
        f"Tied matches:        {tied_matches}"
    )

    print(
        f"No-result matches:   {no_result_matches}"
    )

    print(
        f"Teams:               {len(state['teams'])}"
    )

    print(
        f"Players:             {len(state['players'])}"
    )

    print(
        f"Player performances: "
        f"{len(state['player_match_performances'])}"
    )

    print(
        f"Total deliveries:    {total_deliveries}"
    )

    print(
        f"Total team runs:     {total_team_runs}"
    )

    print(
        f"Players without Cricsheet ID: "
        f"{missing_registry_ids}"
    )

    print()
    print("Generated files:")

    for filename in [
        "match_team_stats.csv",
        "matches.csv",
        "player_match_performance.csv",
        "player_statistics.csv",
        "players.csv",
        "teams.csv",
    ]:

        filepath = (
            OUTPUT_DIR
            / filename
        )

        if filepath.exists():

            print(
                f"  {filename:<35}"
                f"{format_file_size(filepath):>12}"
            )

    print()
    print(
        "Output directory:"
    )

    print(
        OUTPUT_DIR
    )

    print()
    print("=" * 80)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    run_import()